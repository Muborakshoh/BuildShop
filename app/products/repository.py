from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.inventory.models import Inventory
from app.products.models import Category, Product


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def get_by_slug(self, slug: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.slug == slug))

    def list(self) -> list[Category]:
        return list(self.db.scalars(select(Category).order_by(Category.name)).all())

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category), selectinload(Product.inventory))
        )
        return self.db.scalar(stmt)

    def get_by_slug(self, slug: str) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.slug == slug)
            .options(selectinload(Product.category), selectinload(Product.inventory))
        )
        return self.db.scalar(stmt)

    def list(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        stmt: Select[tuple[Product]] = select(Product).options(selectinload(Product.category), selectinload(Product.inventory))
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Product.name.ilike(like), Product.description.ilike(like)))
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if in_stock is not None:
            stmt = stmt.join(Inventory)
            stmt = stmt.where(Inventory.quantity > 0 if in_stock else Inventory.quantity <= 0)
        stmt = stmt.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        self.db.delete(product)
        self.db.commit()

