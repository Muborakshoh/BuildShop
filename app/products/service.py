import re
import unicodedata

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.inventory.models import Inventory
from app.products.models import Category, Product
from app.products.repository import CategoryRepository, ProductRepository
from app.products.schemas import CategoryCreate, CategoryUpdate, ProductCreate, ProductUpdate


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name (supports Cyrillic)."""
    translit = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
        "ғ": "gh", "ӣ": "i", "қ": "q", "ў": "u", "ҳ": "h", "ҷ": "j",
    }
    text = name.lower().strip()
    result = []
    for ch in text:
        if ch in translit:
            result.append(translit[ch])
        elif ch.isascii() and (ch.isalnum() or ch == "-"):
            result.append(ch)
        elif ch in (" ", "_", "/", ".", ","):
            result.append("-")
        # Skip unknown chars (combining marks, etc.)
    slug = re.sub(r"-+", "-", "".join(result)).strip("-")
    return slug or "item"


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    def list_categories(self) -> list[Category]:
        return self.repo.list()

    def create_category(self, data: CategoryCreate) -> Category:
        dump = data.model_dump()
        if not dump.get("slug"):
            dump["slug"] = generate_slug(dump["name"])
        # Ensure unique slug
        base_slug = dump["slug"]
        counter = 1
        while self.repo.get_by_slug(dump["slug"]):
            dump["slug"] = f"{base_slug}-{counter}"
            counter += 1
        try:
            return self.repo.create(Category(**dump))
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{dump['name']}' already exists",
            )

    def update_category(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        try:
            return self.repo.update(category)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate name or slug")

    def delete_category(self, category_id: int) -> None:
        category = self.repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        try:
            self.repo.delete(category)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete category with products",
            )


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.products = ProductRepository(db)
        self.categories = CategoryRepository(db)

    def list_products(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        return self.products.list(search, category_id, min_price, max_price, in_stock, skip, limit)

    def get_product(self, product_id: int) -> Product:
        product = self.products.get(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def create_product(self, data: ProductCreate) -> Product:
        if not self.categories.get(data.category_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        payload = data.model_dump(exclude={"initial_stock"})
        if not payload.get("slug"):
            payload["slug"] = generate_slug(payload["name"])
        # Ensure unique slug
        base_slug = payload["slug"]
        counter = 1
        while self.products.get_by_slug(payload["slug"]):
            payload["slug"] = f"{base_slug}-{counter}"
            counter += 1
        product = Product(**payload)
        product.inventory = Inventory(quantity=data.initial_stock, reserved=0)
        try:
            return self.products.create(product)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product '{payload['name']}' already exists",
            )

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        update_data = data.model_dump(exclude_unset=True)
        if "category_id" in update_data and not self.categories.get(update_data["category_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        for field, value in update_data.items():
            setattr(product, field, value)
        try:
            return self.products.update(product)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate name or slug")

    def delete_product(self, product_id: int) -> None:
        product = self.get_product(product_id)
        self.products.delete(product)
