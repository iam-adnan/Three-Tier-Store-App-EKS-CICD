"""Tests for Product Service"""
import pytest
from fastapi.testclient import TestClient
from app.main import app, products_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    products_db.clear()
    yield
    products_db.clear()


SAMPLE_PRODUCT = {
    "name": "Test Laptop",
    "description": "A great test laptop",
    "price": 999.99,
    "stock": 50,
    "category": "Electronics",
    "image_url": "https://example.com/laptop.jpg",
}


class TestHealth:
    def test_health_returns_200(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        assert res.json()["service"] == "product-service"

    def test_ready_returns_200(self):
        res = client.get("/ready")
        assert res.status_code == 200


class TestCreateProduct:
    def test_create_product_success(self):
        res = client.post("/products", json=SAMPLE_PRODUCT)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Test Laptop"
        assert data["price"] == 999.99
        assert "id" in data
        assert "created_at" in data

    def test_create_product_missing_name(self):
        payload = {**SAMPLE_PRODUCT, "name": ""}
        res = client.post("/products", json=payload)
        assert res.status_code == 422

    def test_create_product_negative_price(self):
        payload = {**SAMPLE_PRODUCT, "price": -10}
        res = client.post("/products", json=payload)
        assert res.status_code == 422

    def test_create_product_negative_stock(self):
        payload = {**SAMPLE_PRODUCT, "stock": -1}
        res = client.post("/products", json=payload)
        assert res.status_code == 422


class TestGetProduct:
    def test_get_product_success(self):
        created = client.post("/products", json=SAMPLE_PRODUCT).json()
        res = client.get(f"/products/{created['id']}")
        assert res.status_code == 200
        assert res.json()["id"] == created["id"]

    def test_get_product_not_found(self):
        res = client.get("/products/nonexistent-id")
        assert res.status_code == 404

    def test_list_products_empty(self):
        res = client.get("/products")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_products_with_category_filter(self):
        client.post("/products", json={**SAMPLE_PRODUCT, "category": "Electronics"})
        client.post("/products", json={**SAMPLE_PRODUCT, "name": "Shirt", "category": "Clothing"})
        res = client.get("/products?category=Electronics")
        assert res.status_code == 200
        assert len(res.json()) == 1
        assert res.json()[0]["category"] == "Electronics"

    def test_list_products_in_stock_filter(self):
        client.post("/products", json={**SAMPLE_PRODUCT, "stock": 10})
        client.post("/products", json={**SAMPLE_PRODUCT, "name": "Out of stock item", "stock": 0})
        res = client.get("/products?in_stock=true")
        assert res.status_code == 200
        assert all(p["stock"] > 0 for p in res.json())


class TestUpdateProduct:
    def test_update_product_price(self):
        created = client.post("/products", json=SAMPLE_PRODUCT).json()
        res = client.patch(f"/products/{created['id']}", json={"price": 799.99})
        assert res.status_code == 200
        assert res.json()["price"] == 799.99
        assert res.json()["name"] == "Test Laptop"  # unchanged

    def test_update_product_not_found(self):
        res = client.patch("/products/nonexistent", json={"price": 100})
        assert res.status_code == 404


class TestDeleteProduct:
    def test_delete_product_success(self):
        created = client.post("/products", json=SAMPLE_PRODUCT).json()
        res = client.delete(f"/products/{created['id']}")
        assert res.status_code == 204
        assert client.get(f"/products/{created['id']}").status_code == 404

    def test_delete_product_not_found(self):
        res = client.delete("/products/nonexistent")
        assert res.status_code == 404


class TestStockReservation:
    def test_reserve_stock_success(self):
        created = client.post("/products", json=SAMPLE_PRODUCT).json()
        res = client.post(f"/products/{created['id']}/reserve?quantity=10")
        assert res.status_code == 200
        assert res.json()["remaining_stock"] == 40

    def test_reserve_stock_insufficient(self):
        created = client.post("/products", json={**SAMPLE_PRODUCT, "stock": 5}).json()
        res = client.post(f"/products/{created['id']}/reserve?quantity=10")
        assert res.status_code == 409

    def test_release_stock(self):
        created = client.post("/products", json=SAMPLE_PRODUCT).json()
        client.post(f"/products/{created['id']}/reserve?quantity=10")
        res = client.post(f"/products/{created['id']}/release?quantity=10")
        assert res.status_code == 200
        assert res.json()["current_stock"] == 50
