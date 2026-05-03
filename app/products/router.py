import os
import uuid

from fastapi import APIRouter, Depends, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.products.models import Category, Product
from app.products.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ProductCreate,
    ProductListItem,
    ProductRead,
    ProductUpdate,
)
from app.products.service import CategoryService, ProductService

router = APIRouter(prefix="/api", tags=["products"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def product_with_stock(product: Product) -> ProductListItem:
    data = ProductRead.model_validate(product).model_dump()
    data["stock_quantity"] = product.inventory.quantity if product.inventory else 0
    return ProductListItem(**data)


# ── Categories
@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return CategoryService(db).list_categories()


@router.post("/categories", response_model=CategoryRead, status_code=201, dependencies=[Depends(require_admin)])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    return CategoryService(db).create_category(payload)


@router.patch("/categories/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_admin)])
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> Category:
    return CategoryService(db).update_category(category_id, payload)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_category(category_id: int, db: Session = Depends(get_db)) -> Response:
    CategoryService(db).delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Products
@router.get("/products", response_model=list[ProductListItem])
def list_products(
    search: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[ProductListItem]:
    products = ProductService(db).list_products(
        search, category_id, min_price, max_price, in_stock, skip, limit
    )
    return [product_with_stock(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductListItem)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductListItem:
    return product_with_stock(ProductService(db).get_product(product_id))


@router.post("/products", response_model=ProductListItem, status_code=201, dependencies=[Depends(require_admin)])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductListItem:
    product = ProductService(db).create_product(payload)
    return product_with_stock(product)


@router.patch("/products/{product_id}", response_model=ProductListItem, dependencies=[Depends(require_admin)])
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> ProductListItem:
    product = ProductService(db).update_product(product_id, payload)
    return product_with_stock(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)) -> Response:
    ProductService(db).delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Image Upload
@router.post("/upload-image", dependencies=[Depends(require_admin)])
async def upload_image(file: UploadFile) -> dict[str, str]:
    ext = os.path.splitext(file.filename or "img.png")[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        return {"error": "Unsupported file type"}
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/{filename}"}
