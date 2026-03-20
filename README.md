# 🛒 Three-Tier Store Application Deployment on EKS using CI/CD

> A production-grade e-commerce microservices platform deployed on AWS EKS using a complete GitOps CI/CD pipeline with automated testing, code quality scanning, container orchestration, service mesh, and real-time monitoring.

![AWS](https://img.shields.io/badge/AWS-EKS-orange?style=for-the-badge&logo=amazon-aws)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.31-blue?style=for-the-badge&logo=kubernetes)
![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-green?style=for-the-badge&logo=argo)
![Python](https://img.shields.io/badge/Python-FastAPI-yellow?style=for-the-badge&logo=python)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple?style=for-the-badge&logo=terraform)

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture Diagram](#architecture-diagram)
- [Tech Stack](#tech-stack)
- [Microservices](#microservices)
- [Folder Structure](#folder-structure)
- [CI/CD Pipeline Flow](#cicd-pipeline-flow)
- [Prerequisites](#prerequisites)
- [Step-by-Step Deployment Guide](#step-by-step-deployment-guide)
  - [Step 1 — GitHub Repository Setup](#step-1--github-repository-setup)
  - [Step 2 — AWS Setup and EKS with Terraform](#step-2--aws-setup-and-eks-with-terraform)
  - [Step 3 — Install Platform Tools on EKS](#step-3--install-platform-tools-on-eks)
  - [Step 4 — SonarQube and First Pipeline Run](#step-4--sonarqube-and-first-pipeline-run)
- [GitHub Secrets Required](#github-secrets-required)
- [Kubernetes Manifests](#kubernetes-manifests)
- [Monitoring and Observability](#monitoring-and-observability)
- [Common Problems and Fixes](#common-problems-and-fixes)
- [How to Destroy Everything](#how-to-destroy-everything)
- [Cost Estimate](#cost-estimate)

---

## Project Overview

This project deploys a fully functional e-commerce application as microservices on AWS EKS. Every git push automatically triggers a CI/CD pipeline that runs tests, scans code quality, builds Docker images, pushes to ECR, and deploys to Kubernetes through ArgoCD — with Slack notifications at every stage.

**What makes this project impressive for a portfolio:**
- Real microservices with inter-service communication
- GitOps deployment pattern using ArgoCD
- Istio service mesh with mTLS, circuit breakers, and traffic management
- SonarQube code quality gates blocking bad deployments
- Horizontal Pod Autoscaling on every service
- Full observability with Prometheus and Grafana
- Infrastructure as Code with Terraform

---

## Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER WORKFLOW                              │
│                                                                         │
│   git push → GitHub ──────────────────────────────────────────────────▶│
│                │                                                        │
│                ▼                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │              GitHub Actions CI/CD Pipeline                     │   │
│   │                                                                │   │
│   │  ┌─────────────┐   ┌──────────────┐   ┌───────────────────┐  │   │
│   │  │ Run pytest  │──▶│  SonarQube   │──▶│  Build & Push     │  │   │
│   │  │ 4 services  │   │  Quality     │   │  Docker → ECR     │  │   │
│   │  │ in parallel │   │  Gate Check  │   │  5 images         │  │   │
│   │  └─────────────┘   └──────────────┘   └─────────┬─────────┘  │   │
│   │         │                                        │            │   │
│   │         ▼                                        ▼            │   │
│   │  ┌─────────────┐                    ┌───────────────────────┐ │   │
│   │  │    Slack    │                    │  Update K8s manifest  │ │   │
│   │  │  ✅ Tests   │                    │  image tag in repo    │ │   │
│   │  │  passed!    │                    └───────────┬───────────┘ │   │
│   │  └─────────────┘                               │             │   │
│   └────────────────────────────────────────────────┼─────────────┘   │
│                                                     │                  │
│                          ArgoCD watches repo ◀──────┘                  │
│                                │                                       │
│                                ▼                                       │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    AWS EKS Cluster                             │   │
│   │                                                                │   │
│   │   Internet ──▶ Istio Gateway ──▶ shopwave namespace           │   │
│   │                                        │                      │   │
│   │                          ┌─────────────▼──────────────────┐   │   │
│   │                          │         api-gateway            │   │   │
│   │                          │      (LoadBalancer svc)        │   │   │
│   │                          └──┬──────┬──────┬──────┬────────┘   │   │
│   │                             │      │      │      │            │   │
│   │                   ┌─────────▼┐ ┌───▼──┐ ┌▼────┐ ┌▼────────┐  │   │
│   │                   │ product  │ │ cart │ │order│ │payment  │  │   │
│   │                   │ service  │ │ svc  │ │ svc │ │  svc    │  │   │
│   │                   │ HPA 2-10 │ │HPA   │ │HPA  │ │  HPA    │  │   │
│   │                   └──────────┘ └──────┘ └─────┘ └─────────┘  │   │
│   │                                                                │   │
│   │   ┌─────────────────────────────────────────────────────┐     │   │
│   │   │           monitoring namespace                      │     │   │
│   │   │  Prometheus ──scrapes──▶ all pods                   │     │   │
│   │   │  Grafana ──▶ dashboards (latency, errors, HPA)     │     │   │
│   │   │  Alertmanager ──▶ Slack #alerts-critical            │     │   │
│   │   └─────────────────────────────────────────────────────┘     │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   Slack Notifications:                                                  │
│   ✅ All tests passed   🚀 Deployment triggered   ⚠️ Alert firing      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Microservices | Python 3.11 + FastAPI | 5 independent services |
| Testing | pytest + pytest-cov | Unit tests with coverage |
| Code Quality | SonarQube Cloud | Quality gates, bugs, security |
| Containers | Docker | Package each service |
| Registry | AWS ECR | Store Docker images |
| Infrastructure | Terraform | Provision all AWS resources |
| Orchestration | AWS EKS (Kubernetes 1.31) | Run containers at scale |
| GitOps | ArgoCD | Auto-deploy on git push |
| Service Mesh | Istio | mTLS, circuit breaker, retries |
| Autoscaling | Kubernetes HPA | Scale pods on CPU/memory |
| CI/CD | GitHub Actions | Automate entire pipeline |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Alerting | Alertmanager + Slack | Real-time alerts |
| Notifications | Slack webhooks | Test and deploy results |

---

## Microservices

| Service | Port | Responsibility |
|---|---|---|
| `api-gateway` | 8000 | Single entry point, routing, rate limiting (100 req/min) |
| `product-service` | 8000 | Product catalog, stock reservation and release |
| `cart-service` | 8000 | Shopping cart, talks to product service for stock check |
| `order-service` | 8000 | Order lifecycle, saga pattern orchestration |
| `payment-service` | 8000 | Payment processing, refunds, payment history |

All services expose `/health` and `/ready` endpoints for Kubernetes probes.

---

## Folder Structure
```
Three-Tier-Store-App-EKS-CICD/
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml                    # Complete CI/CD pipeline
│
├── services/
│   ├── product-service/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py                  # FastAPI application
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_main.py             # pytest test suite
│   │   ├── conftest.py                  # pytest path configuration
│   │   ├── pytest.ini                   # pytest settings
│   │   ├── sonar-project.properties     # SonarQube config
│   │   ├── requirements.txt             # Python dependencies
│   │   └── Dockerfile                   # Container definition
│   │
│   ├── cart-service/                    # Same structure as product
│   ├── order-service/                   # Same structure as product
│   ├── payment-service/                 # Same structure as product
│   └── api-gateway/                     # Same structure as product
│
├── k8s/
│   ├── base/
│   │   ├── namespace/
│   │   │   └── namespace.yaml           # shopwave namespace + Istio label
│   │   ├── product-svc/
│   │   │   └── deployment.yaml          # Deployment + Service + HPA
│   │   ├── cart-svc/
│   │   │   └── deployment.yaml
│   │   ├── order-svc/
│   │   │   └── deployment.yaml
│   │   ├── payment-svc/
│   │   │   └── deployment.yaml
│   │   └── gateway-svc/
│   │       └── deployment.yaml          # LoadBalancer service
│   │
│   ├── argocd/
│   │   ├── root-app.yaml                # App-of-Apps root application
│   │   ├── argocd-config.yaml           # Project + Slack notifications
│   │   └── apps/
│   │       ├── product-service.yaml     # ArgoCD Application per service
│   │       ├── cart-service.yaml
│   │       ├── order-service.yaml
│   │       ├── payment-service.yaml
│   │       └── api-gateway.yaml
│   │
│   ├── istio/
│   │   └── istio-config.yaml            # Gateway, VirtualServices, DestinationRules, mTLS
│   │
│   └── monitoring/
│       ├── prometheus/
│       │   ├── prometheus-config.yaml   # Scrape configs + alert rules
│       │   └── prometheus-deploy.yaml   # Prometheus + Alertmanager
│       └── grafana/
│           └── grafana-deploy.yaml      # Grafana + dashboards
│
├── terraform/
│   ├── main.tf                          # VPC, EKS, ECR, IAM
│   ├── variables.tf                     # Input variables
│   └── terraform.tfvars                 # Your values (gitignored)
│
├── scripts/
│   └── setup.sh                         # One-command bootstrap
│
├── docker-compose.yml                   # Local development
├── Makefile                             # Shortcut commands
├── .gitignore
└── README.md
```

---

## CI/CD Pipeline Flow
```
git push to main
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  Job 1: Detect Changed Services (4s)                │
│  Checks which service folders changed               │
│  Sets outputs: product=true, cart=true etc          │
└───────────────────────┬─────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Test    │  │  Test    │  │  Test    │  (parallel)
    │ product  │  │  cart    │  │  order   │
    │ service  │  │ service  │  │ service  │
    │ ~1 min   │  │ ~1 min   │  │ ~1 min   │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │  pytest     │  pytest     │  pytest
         │  coverage   │  coverage   │  coverage
         │  sonarqube  │  sonarqube  │  sonarqube
         └─────────────┴─────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Slack — Test Results   │
          │  ✅ All tests passed!   │
          │  or ❌ Tests FAILED     │
          └─────────────┬───────────┘
                        │ (only if all tests pass)
                        ▼
    ┌───────────────────────────────────────────┐
    │  Build & Push (5 parallel matrix jobs)    │
    │  product / cart / order / payment /       │
    │  api-gateway → AWS ECR                    │
    └───────────────────┬───────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Update K8s Manifests   │
          │  sed IMAGE_TAG → sha    │
          │  git commit + push      │
          └─────────────┬───────────┘
                        │
                        ▼ ArgoCD detects change
          ┌─────────────────────────┐
          │  Slack — Deployment     │
          │  🚀 Deployment          │
          │  triggered!             │
          └─────────────────────────┘
                        │
                        ▼ (ArgoCD auto-syncs)
          ┌─────────────────────────┐
          │  EKS — Rolling Update   │
          │  New pods created       │
          │  Old pods terminated    │
          │  Zero downtime deploy   │
          └─────────────────────────┘
```

---

## Prerequisites

Before starting make sure these are installed on your computer:

| Tool | Version | Install |
|---|---|---|
| AWS CLI | v2+ | https://aws.amazon.com/cli/ |
| kubectl | 1.28+ | https://kubernetes.io/docs/tasks/tools/ |
| Terraform | 1.6+ | https://developer.hashicorp.com/terraform/install |
| Helm | 3+ | https://helm.sh/docs/intro/install/ |
| eksctl | latest | https://eksctl.io/installation/ |
| Git | any | https://git-scm.com/ |
| Docker Desktop | any | https://www.docker.com/products/docker-desktop/ |

---

## Step-by-Step Deployment Guide

### Step 1 — GitHub Repository Setup

**1. Create the repository:**
```
Name: Three-Tier-Store-App-EKS-CICD
Visibility: Public
```

**2. Clone and create folder structure:**
```bash
git clone https://github.com/YOUR_USERNAME/Three-Tier-Store-App-EKS-CICD
cd Three-Tier-Store-App-EKS-CICD

# Create all folders
mkdir -p services/{product-service,cart-service,order-service,payment-service,api-gateway}/{app,tests}
mkdir -p k8s/{base/{product-svc,cart-svc,order-svc,payment-svc,gateway-svc,namespace},argocd/apps,istio,monitoring/{prometheus,grafana}}
mkdir -p terraform .github/workflows scripts
```

**3. Add all service files** — each service needs:
- `app/main.py` — FastAPI application code
- `app/__init__.py` — empty file
- `tests/test_main.py` — pytest test suite
- `tests/__init__.py` — empty file
- `conftest.py` — pytest path setup
- `pytest.ini` — pytest configuration
- `sonar-project.properties` — SonarQube config
- `requirements.txt` — Python dependencies
- `Dockerfile` — container definition

**4. Requirements for every service:**
```
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.7.0
httpx==0.27.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==5.0.0
anyio==4.4.0
```

**5. pytest.ini for every service** (save without BOM encoding):
```ini
[pytest]
testpaths = tests
pythonpath = .
asyncio_mode = auto
```

**6. conftest.py for every service:**
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

**7. Dockerfile for every service:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**8. Push to GitHub:**
```bash
git add .
git commit -m "feat: initial project structure"
git push origin main
```

---

### Step 2 — AWS Setup and EKS with Terraform

**1. Configure AWS CLI:**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, region: us-east-1, format: json
```

**2. Create Terraform backend:**
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws s3api create-bucket \
  --bucket shopwave-terraform-state-${ACCOUNT_ID} \
  --region us-east-1 \
  --create-bucket-configuration LocationConstraint=us-east-1

aws s3api put-bucket-versioning \
  --bucket shopwave-terraform-state-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name shopwave-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**3. Update terraform/main.tf backend block:**
```hcl
backend "s3" {
  bucket         = "shopwave-terraform-state-491325670828"  # your account ID
  key            = "eks/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "shopwave-terraform-locks"
}
```

**4. Create terraform/terraform.tfvars:**
```hcl
aws_region   = "us-east-1"
cluster_name = "shopwave-eks"
environment  = "production"
github_org   = "YOUR_GITHUB_USERNAME"
github_repo  = "Three-Tier-Store-App-EKS-CICD"
```

**5. Deploy infrastructure (takes 15-20 minutes):**
```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

**6. Connect kubectl:**
```bash
aws eks update-kubeconfig --name shopwave-eks --region us-east-1
kubectl get nodes   # verify all nodes show Ready
```

**7. Grant ECR pull permission to nodes:**
```bash
NODEGROUPS=$(aws eks list-nodegroups --cluster-name shopwave-eks --region us-east-1 --query "nodegroups" --output text)

for ng in $NODEGROUPS; do
  ROLE=$(aws eks describe-nodegroup \
    --cluster-name shopwave-eks \
    --nodegroup-name $ng \
    --region us-east-1 \
    --query "nodegroup.nodeRole" \
    --output text)
  ROLE_NAME=$(echo $ROLE | cut -d'/' -f2)
  aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
  echo "Attached ECR policy to $ROLE_NAME"
done
```

**8. Update deployment manifests with real values:**
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TAG=$(aws ecr describe-images \
  --repository-name shopwave/product-service \
  --region us-east-1 \
  --query "sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]" \
  --output text)

for svc in product cart order payment; do
  sed -i "s/YOUR_ACCOUNT_ID/$ACCOUNT_ID/g" k8s/base/${svc}-svc/deployment.yaml
  sed -i "s/YOUR_IMAGE_TAG/$TAG/g" k8s/base/${svc}-svc/deployment.yaml
done

sed -i "s/YOUR_ACCOUNT_ID/$ACCOUNT_ID/g" k8s/base/gateway-svc/deployment.yaml
sed -i "s/YOUR_IMAGE_TAG/$TAG/g" k8s/base/gateway-svc/deployment.yaml
```

---

### Step 3 — Install Platform Tools on EKS

**1. Create namespaces:**
```bash
kubectl apply -f k8s/base/namespace/namespace.yaml
kubectl create namespace monitoring
kubectl create namespace argocd
```

**2. Install Istio:**
```bash
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
export PATH="$PWD/istio-1.20.0/bin:$PATH"
istioctl install --set profile=demo -y
kubectl label namespace shopwave istio-injection=enabled
kubectl apply -f k8s/istio/istio-config.yaml
```

**3. Install ArgoCD:**
```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

**4. Install Prometheus and Grafana:**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.enabled=false \
  --wait

helm install grafana grafana/grafana \
  --namespace monitoring \
  --set adminPassword=shopwave-grafana-2024 \
  --set service.type=LoadBalancer \
  --wait
```

**5. Apply ArgoCD apps:**
```bash
# Replace YOUR_GITHUB_USERNAME first in all argocd yaml files
kubectl apply -f k8s/argocd/argocd-config.yaml
kubectl apply -f k8s/argocd/root-app.yaml
kubectl apply -f k8s/argocd/apps/
```

**6. Apply manifests directly:**
```bash
kubectl apply -f k8s/base/product-svc/deployment.yaml
kubectl apply -f k8s/base/cart-svc/deployment.yaml
kubectl apply -f k8s/base/order-svc/deployment.yaml
kubectl apply -f k8s/base/payment-svc/deployment.yaml
kubectl apply -f k8s/base/gateway-svc/deployment.yaml
```

**7. Verify everything is running:**
```bash
kubectl get pods -n shopwave
kubectl get pods -n argocd
kubectl get pods -n monitoring
kubectl get pods -n istio-system
```

---

### Step 4 — SonarQube and First Pipeline Run

**1. Create SonarQube Cloud account:**
- Go to sonarcloud.io → Sign in with GitHub
- Create organization → Import your repo
- Choose "With GitHub Actions"
- Copy the SONAR_TOKEN

**2. Add all GitHub Secrets** (repo → Settings → Secrets → Actions):

| Secret | Value |
|---|---|
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `AWS_ACCESS_KEY_ID` | From IAM user CSV |
| `AWS_SECRET_ACCESS_KEY` | From IAM user CSV |
| `SLACK_WEBHOOK_URL` | From api.slack.com |
| `SONAR_TOKEN` | From SonarQube Cloud |
| `SONAR_HOST_URL` | https://sonarcloud.io |
| `ARGOCD_SERVER` | ArgoCD LoadBalancer URL |
| `ARGOCD_PASSWORD` | ArgoCD admin password |
| `GH_PAT` | GitHub Personal Access Token |
| `GRAFANA_URL` | Grafana LoadBalancer URL |

**3. Trigger pipeline:**
```bash
git add .
git commit -m "feat: trigger first CI/CD pipeline run"
git push origin main
```

**4. Watch it run** in GitHub → Actions tab.

---

## GitHub Secrets Required
```
AWS_ACCOUNT_ID          → 12-digit AWS account number
AWS_ACCESS_KEY_ID       → IAM user access key
AWS_SECRET_ACCESS_KEY   → IAM user secret key
SLACK_WEBHOOK_URL       → Slack incoming webhook URL
SONAR_TOKEN             → SonarQube authentication token
SONAR_HOST_URL          → https://sonarcloud.io
ARGOCD_SERVER           → ArgoCD server hostname/IP
ARGOCD_PASSWORD         → ArgoCD admin password
GH_PAT                  → GitHub PAT with repo scope
GRAFANA_URL             → Grafana server URL
```

---

## Kubernetes Manifests

Each deployment manifest contains three resources:

**1. Deployment** — defines the pod template, image, environment variables, resource limits, health checks:
```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
livenessProbe:
  httpGet:
    path: /health
    port: 8000
```

**2. Service** — ClusterIP for internal services, LoadBalancer for api-gateway:
```yaml
type: ClusterIP   # internal services
type: LoadBalancer  # api-gateway only
```

**3. HorizontalPodAutoscaler** — scales pods automatically:
```yaml
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

---

## Monitoring and Observability

**Prometheus** scrapes metrics from all pods every 15 seconds.

**Alert rules configured:**
- Service down for more than 1 minute → Slack #alerts-critical
- Error rate above 5% → Slack #alerts-warnings
- p95 latency above 2 seconds → Slack #alerts-warnings
- Pod crash looping → Slack #alerts-critical
- Payment failure rate above 10% → Slack #alerts-payments
- HPA at maximum replicas → Slack #alerts-warnings

**Access Grafana:**
```bash
kubectl get svc grafana -n monitoring
# Open EXTERNAL-IP:3000
# Login: admin / shopwave-grafana-2024
```

**Access Prometheus:**
```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Open http://localhost:9090
```

---

## Common Problems and Fixes

During this project we encountered and solved the following real issues:

### 1. Terraform — Kubernetes version 1.28 AMI not found
**Error:** `Requested AMI for this version 1.28 is not supported`
**Cause:** AWS deprecated Kubernetes 1.28 AMIs in us-east-1.
**Fix:** Change `cluster_version = "1.28"` to `cluster_version = "1.31"` in main.tf.

### 2. Terraform — t3.medium instance type not available
**Error:** `The specified instance type is not eligible for Free Tier`
**Cause:** New AWS accounts have EC2 instance quota limits.
**Fix:** Change instance type to `t3.small` and request quota increase in AWS Service Quotas console.

### 3. Terraform — aws-ebs-csi-driver addon timeout
**Error:** `waiting for EKS Add-On create: timeout`
**Cause:** The addon requires an IAM service account that Terraform does not create automatically.
**Fix:** Remove addon from Terraform, install manually with eksctl after cluster is up:
```bash
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster shopwave-eks \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve
aws eks create-addon --cluster-name shopwave-eks --addon-name aws-ebs-csi-driver
```

### 4. Terraform — DNS resolution failure for AWS endpoints
**Error:** `dial tcp: lookup ec2.us-east-1.amazonaws.com: no such host`
**Cause:** Windows DNS cache corruption after system restart.
**Fix:**
```powershell
ipconfig /flushdns
netsh winsock reset
netsh interface ip set dns "Wi-Fi" static 8.8.8.8
```

### 5. GitHub Actions — actions/upload-artifact@v3 deprecated
**Error:** `This request has been automatically failed because it uses a deprecated version`
**Fix:** Change all `actions/upload-artifact@v3` to `actions/upload-artifact@v4` in ci-cd.yml.

### 6. GitHub Actions — pytest command not found
**Error:** `pytest: command not found` (exit code 127)
**Cause:** pip installs pytest but it is not on the system PATH in GitHub Actions runners.
**Fix:** Use `python -m pytest` instead of `pytest` in every test step.

### 7. GitHub Actions — pytest.ini BOM encoding error
**Error:** `unexpected line: '\ufeff[pytest]'`
**Cause:** PowerShell `Set-Content` on Windows adds a BOM (Byte Order Mark) character. Linux cannot read it.
**Fix:** Use `[System.IO.File]::WriteAllText()` instead of `Set-Content` on Windows, or edit files directly on GitHub in the browser.

### 8. SonarQube — sonar.organization missing
**Error:** `You must define the following mandatory properties: sonar.organization`
**Fix:** Add `sonar.organization=YOUR_GITHUB_USERNAME` to every `sonar-project.properties` file.

### 9. pytest — collected 0 items
**Error:** `no tests ran` even though test files exist.
**Cause:** Missing `__init__.py` files in `app/` and `tests/` folders, or empty test files.
**Fix:** Create empty `__init__.py` in both folders. Verify `test_main.py` has actual test content.

### 10. ArgoCD — apps Synced but no pods created
**Error:** All ArgoCD apps show Synced/Healthy but `kubectl get pods -n shopwave` returns nothing.
**Cause:** deployment.yaml files were empty or contained `IMAGE_TAG` and `ACCOUNT_ID` placeholders that were never replaced.
**Fix:** Populate deployment.yaml files with real content, replace placeholders with actual AWS account ID and ECR image tag, push to GitHub.

### 11. Pods Degraded — ImagePullBackOff
**Error:** Pods crash with `ImagePullBackOff`
**Cause:** EKS node IAM roles did not have permission to pull from ECR.
**Fix:** Attach `AmazonEC2ContainerRegistryReadOnly` policy to all node group IAM roles.

---

## How to Destroy Everything

**Clean up Kubernetes load balancers first** (otherwise VPC deletion fails):
```bash
kubectl delete svc api-gateway -n shopwave
kubectl delete svc argocd-server -n argocd
kubectl delete svc grafana -n monitoring
kubectl delete svc istio-ingressgateway -n istio-system
sleep 30
```

**Destroy all AWS infrastructure:**
```bash
cd terraform
terraform destroy -auto-approve
```

**Delete Terraform state storage** (optional):
```bash
aws s3 rb s3://shopwave-terraform-state-YOUR_ACCOUNT_ID --force
aws dynamodb delete-table --table-name shopwave-terraform-locks --region us-east-1
```

---

## Cost Estimate

| Resource | Monthly Cost |
|---|---|
| EKS cluster control plane | ~$73 |
| EC2 t3.small nodes (3x) | ~$45 |
| NAT Gateway | ~$32 |
| Load Balancers (3x) | ~$54 |
| ECR storage | ~$1 |
| S3 + DynamoDB (Terraform state) | ~$0.10 |
| **Total** | **~$205/month** |

> To reduce cost: use `t3.micro` nodes, single NAT gateway (`single_nat_gateway = true` in Terraform), and destroy the cluster when not in use.

---

## What I Learned

Building this project from scratch taught me:

- How GitOps works in practice — the git repository is the single source of truth for cluster state
- Why ArgoCD is powerful — it continuously reconciles desired state (git) with actual state (cluster)
- How Istio service mesh adds security and reliability without changing application code
- The importance of IAM permissions — most production issues come down to missing permissions
- How to debug Kubernetes deployments systematically — events, logs, describe, get
- Why Infrastructure as Code matters — being able to recreate the entire platform in 20 minutes
- How CI/CD pipelines catch problems early — tests running on every push prevented bad code reaching production

---

## Author

**Adnan** — Built as a portfolio project demonstrating production-grade DevOps and cloud engineering skills.

- GitHub: [@iam-adnan](https://github.com/iam-adnan)
- Project: [Three-Tier-Store-App-EKS-CICD](https://github.com/iam-adnan/Three-Tier-Store-App-EKS-CICD)

---

*Built with AWS EKS, Terraform, ArgoCD, Istio, GitHub Actions, SonarQube, Prometheus, Grafana, and FastAPI*
