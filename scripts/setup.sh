#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# ShopWave — Bootstrap Script
# Runs once to set up the entire platform from scratch.
# Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Config ────────────────────────────────────────────────────────────────────
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="${CLUSTER_NAME:-shopwave-eks}"
GITHUB_USERNAME="${GITHUB_USERNAME:-YOUR_GITHUB_USERNAME}"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   ShopWave Platform Bootstrap        ║"
echo "║   EKS + ArgoCD + Istio + Monitoring  ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Check prerequisites ────────────────────────────────────────────────────
info "Checking prerequisites..."
for cmd in aws kubectl helm terraform git; do
  command -v $cmd &>/dev/null || error "$cmd is not installed. Please install it first."
done
success "All prerequisites installed"

# ── 2. Terraform: Create S3 backend for state ─────────────────────────────────
info "Creating Terraform state backend..."
aws s3api create-bucket \
  --bucket shopwave-terraform-state \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION 2>/dev/null || warn "S3 bucket already exists"

aws s3api put-bucket-versioning \
  --bucket shopwave-terraform-state \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name shopwave-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION 2>/dev/null || warn "DynamoDB table already exists"

success "Terraform backend ready"

# ── 3. Terraform: Provision EKS ───────────────────────────────────────────────
info "Provisioning EKS cluster with Terraform (this takes ~15 minutes)..."
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
cd ..
success "EKS cluster provisioned"

# ── 4. Configure kubectl ──────────────────────────────────────────────────────
info "Configuring kubectl..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION
kubectl cluster-info
success "kubectl configured"

# ── 5. Install Istio ──────────────────────────────────────────────────────────
info "Installing Istio..."
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
export PATH="$PWD/istio-1.20.0/bin:$PATH"
istioctl install --set profile=production -y
kubectl label namespace shopwave istio-injection=enabled --overwrite
success "Istio installed"

# ── 6. Install ArgoCD ─────────────────────────────────────────────────────────
info "Installing ArgoCD..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

info "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)
echo ""
echo "  ArgoCD admin password: $ARGOCD_PASSWORD"
echo "  Save this! You will need it for the CI pipeline secret ARGOCD_PASSWORD"
echo ""
success "ArgoCD installed"

# ── 7. Install ArgoCD Notifications ───────────────────────────────────────────
info "Installing ArgoCD Notifications..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-notifications/release-1.2/manifests/install.yaml
kubectl apply -n argocd -f k8s/argocd/argocd-config.yaml
success "ArgoCD Notifications installed"

# ── 8. Install Prometheus + Grafana ───────────────────────────────────────────
info "Installing Prometheus stack..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/monitoring/prometheus/
kubectl apply -f k8s/monitoring/grafana/
success "Monitoring stack installed"

# ── 9. Apply ShopWave base manifests ──────────────────────────────────────────
info "Applying ShopWave K8s manifests..."
kubectl apply -f k8s/base/namespace/namespace.yaml
kubectl apply -f k8s/istio/istio-config.yaml
success "Base manifests applied"

# ── 10. Apply ArgoCD root app (triggers all deployments) ─────────────────────
info "Applying ArgoCD root application..."
sed -i "s/YOUR_GITHUB_USERNAME/$GITHUB_USERNAME/g" k8s/argocd/root-app.yaml
kubectl apply -f k8s/argocd/root-app.yaml
kubectl apply -f k8s/argocd/apps/
success "ArgoCD root application applied"

# ── 11. Get service URLs ───────────────────────────────────────────────────────
info "Fetching service endpoints..."
echo ""
echo "Waiting for LoadBalancer IP (this may take 2-3 minutes)..."
sleep 60

GATEWAY_URL=$(kubectl get svc api-gateway -n shopwave \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
ARGOCD_URL=$(kubectl get svc argocd-server -n argocd \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
GRAFANA_URL=$(kubectl get svc grafana -n monitoring \
  -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "internal-only")

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              ShopWave Platform is READY!                 ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  API Gateway:  http://$GATEWAY_URL"
echo "║  ArgoCD UI:    https://$ARGOCD_URL"
echo "║  Grafana:      http://$(kubectl get svc -n monitoring grafana -o jsonpath='{.spec.clusterIP}'):3000"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  ArgoCD password: $ARGOCD_PASSWORD"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Next: Add these GitHub Secrets to your repo:           ║"
echo "║    AWS_ACCOUNT_ID     AWS_ACCESS_KEY_ID                 ║"
echo "║    AWS_SECRET_ACCESS_KEY  SLACK_WEBHOOK_URL             ║"
echo "║    SONAR_TOKEN        SONAR_HOST_URL                    ║"
echo "║    ARGOCD_SERVER      ARGOCD_PASSWORD                   ║"
echo "║    GH_PAT             GRAFANA_URL                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
