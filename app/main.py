import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.cashier.router import router as cashier_router
from app.cms import models as _cms_models  # noqa: F401 — register CMS tables
from app.cms.router import router as cms_router
from app.core.bootstrap import bootstrap_first_admin
from app.core.config import settings
from app.db.session import SessionLocal
from app.inventory.router import router as inventory_router
from app.orders.router import router as orders_router
from app.products.router import router as products_router
from app.users.router import router as users_router

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
    app.include_router(cms_router)

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
    return app


app = create_app()
