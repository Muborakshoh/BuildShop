import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.auth.router import router as auth_router
from app.cashier.router import router as cashier_router
from app.core.bootstrap import bootstrap_first_admin
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.inventory.router import router as inventory_router
from app.orders.router import router as orders_router
from app.products.router import router as products_router
from app.users.router import router as users_router

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def migrate_tables() -> None:
    """Add missing columns to existing tables (simple migration)."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        # Products table — add unit and volume if missing
        if inspector.has_table("products"):
            existing = {c["name"] for c in inspector.get_columns("products")}
            if "unit" not in existing:
                conn.execute(text("ALTER TABLE products ADD COLUMN unit VARCHAR(20) NOT NULL DEFAULT 'шт'"))
            if "volume" not in existing:
                conn.execute(text("ALTER TABLE products ADD COLUMN volume VARCHAR(50)"))
        # Categories table — add image_url if missing
        if inspector.has_table("categories"):
            existing = {c["name"] for c in inspector.get_columns("categories")}
            if "image_url" not in existing:
                conn.execute(text("ALTER TABLE categories ADD COLUMN image_url VARCHAR(500)"))


def create_app() -> FastAPI:
    app = FastAPI(
        title="BuildShop API",
        description="Modular monolith backend for a construction materials store.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        migrate_tables()
        db = SessionLocal()
        try:
            bootstrap_first_admin(db)
        finally:
            db.close()

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(products_router)
    app.include_router(orders_router)
    app.include_router(inventory_router)
    app.include_router(cashier_router)

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
    return app


app = create_app()
