test:
	cd services/product-service && pytest tests/ -v
	cd services/cart-service && pytest tests/ -v
	cd services/order-service && pytest tests/ -v
	cd services/payment-service && pytest tests/ -v

run:
	docker-compose up --build

setup:
	chmod +x scripts/setup.sh && ./scripts/setup.sh
