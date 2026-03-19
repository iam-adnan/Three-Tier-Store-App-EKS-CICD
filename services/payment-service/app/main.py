"""
ShopWave — Product Service
Handles product catalog: CRUD, search, inventory
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ShopWave Product Service",
    version="1.0.0",
    description="Product catalog microservice",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory store (replace with RDS/DynamoDB in production) ─────────────────
products_db: dict = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1)
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    image_url: Optional[str] = None


class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "service": "product-service", "version": "1.0.0"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/products", response_model=List[Product])
def list_products(
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items = list(products_db.values())
    if category:
        items = [p for p in items if p["category"].lower() == category.lower()]
    if min_price is not None:
        items = [p for p in items if p["price"] >= min_price]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]
    if in_stock is not None:
        items = [p for p in items if (p["stock"] > 0) == in_stock]
    return items[offset: offset + limit]


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products", response_model=Product, status_code=201)
def create_product(data: ProductCreate):
    product_id = str(uuid.uuid4())
    now = datetime.utcnow()
    product = {
        "id": product_id,
        **data.dict(),
        "created_at": now,
        "updated_at": now,
    }
    products_db[product_id] = product
    logger.info(f"Created product {product_id}: {data.name}")
    return product


@app.patch("/products/{product_id}", response_model=Product)
def update_product(product_id: str, data: ProductUpdate):
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    product.update(updates)
    product["updated_at"] = datetime.utcnow()
    products_db[product_id] = product
    return product


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]


@app.post("/products/{product_id}/reserve")
def reserve_stock(product_id: str, quantity: int = Query(..., ge=1)):
    """Called by order service to reserve stock."""
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product["stock"] < quantity:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    product["stock"] -= quantity
    product["updated_at"] = datetime.utcnow()
    logger.info(f"Reserved {quantity} units of product {product_id}")
    return {"reserved": True, "remaining_stock": product["stock"]}


@app.post("/products/{product_id}/release")
def release_stock(product_id: str, quantity: int = Query(..., ge=1)):
    """Called by order service to release stock on order cancellation."""
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["stock"] += quantity
    product["updated_at"] = datetime.utcnow()
    return {"released": True, "current_stock": product["stock"]}
