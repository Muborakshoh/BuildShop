import os

from fastapi import FastAPI
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.cashier.router import router as cashier_router
from app.cashier import models as _cashier_models  # noqa: F401
from app.cms import models as _cms_models  # noqa: F401
from app.reviews import models as _reviews_models  # noqa: F401
from app.promos import models as _promos_models  # noqa: F401 — register CMS tables
from app.cms.router import router as cms_router
from app.cms.models import PageStatus
from app.cms.service import NewsService, PageService
from app.core.bootstrap import bootstrap_first_admin
from app.core.config import settings
from app.db.session import SessionLocal
from app.inventory.router import router as inventory_router
from app.orders.router import router as orders_router
from app.products.router import router as products_router
from app.users.router import router as users_router
from app.reviews.router import router as reviews_router
from app.promos.router import router as promos_router
from app.telegram.router import router as telegram_router
from app.delivery.router import router as delivery_router
from app.delivery import models as _delivery_models  # noqa: F401

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
        settings.validate_secret_key()
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
    app.include_router(reviews_router)
    app.include_router(promos_router)
    app.include_router(telegram_router)
    app.include_router(delivery_router)

    # --- User documentation endpoint ---
    # Try multiple possible docs locations
    _docs_candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs"),
        os.path.join(os.getcwd(), "docs"),
        "/code/docs",
    ]
    DOCS_DIR = next((d for d in _docs_candidates if os.path.isdir(d)), _docs_candidates[0])

    @app.get("/api/guide/{lang}/{filename}", include_in_schema=False)
    def get_doc(lang: str, filename: str) -> Response:
        if lang not in ("tj", "ru", "en"):
            return Response(content="Language not found", status_code=404)
        # Sanitize filename
        safe_name = os.path.basename(filename)
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        filepath = os.path.join(DOCS_DIR, lang, safe_name)
        if not os.path.isfile(filepath):
            return Response(content="Document not found", status_code=404)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/plain; charset=utf-8")

    @app.get("/sitemap.xml", include_in_schema=False)
    def sitemap_xml() -> Response:
        db = SessionLocal()
        try:
            pages = PageService(db).list_pages(status=PageStatus.PUBLISHED)
            news = NewsService(db).list_news(status=PageStatus.PUBLISHED, limit=200)
            from app.products.service import ProductService

            products = ProductService(db).list_products(limit=500)
            urls = ["/", "/pages/products.html", "/pages/categories.html", "/pages/news.html"]
            urls.extend(f"/pages/page.html?slug={p.slug}" for p in pages if getattr(p, "robots_index", True))
            urls.extend(f"/pages/news.html?slug={n.slug}" for n in news)
            urls.extend(f"/pages/product.html?id={p.id}" for p in products if getattr(p, "robots_index", True))
            base = settings.site_url.rstrip("/")
            body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            for url in urls:
                loc = url if url.startswith("http") else f"{base}{url}"
                body += f"  <url><loc>{loc}</loc></url>\n"
            body += "</urlset>\n"
            return Response(content=body, media_type="application/xml")
        finally:
            db.close()

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    # Serve Vue SPA from dist/ if it exists, otherwise fall back to old static
    DIST_DIR = os.path.join(os.path.dirname(__file__), "static", "dist")
    if os.path.isdir(DIST_DIR):
        app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="vue-assets")

        # SPA fallback via middleware — does NOT intercept /docs, /redoc, /openapi.json, /api/*
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request as StarletteRequest

        SKIP_PREFIXES = ("/api/", "/docs", "/redoc", "/openapi.json", "/assets/", "/uploads/", "/sitemap.xml")

        # Cache index.html at import time to avoid reading from disk on every 404
        _index_path = os.path.join(DIST_DIR, "index.html")
        with open(_index_path, "r") as _f:
            _cached_index_html = _f.read()

        class SPAMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: StarletteRequest, call_next):
                response = await call_next(request)
                path = request.url.path
                # If 404 and not an API/docs/static path, serve SPA index.html
                if response.status_code == 404 and not any(path.startswith(p) for p in SKIP_PREFIXES):
                    # Try old static file first
                    old_static = os.path.join(os.path.dirname(__file__), "static")
                    file_path = os.path.join(old_static, path.lstrip("/"))
                    if path.lstrip("/") and os.path.isfile(file_path):
                        import mimetypes
                        mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                        with open(file_path, "rb") as f:
                            return Response(content=f.read(), media_type=mime)
                    # Serve cached Vue SPA index
                    return Response(content=_cached_index_html, media_type="text/html")
                return response

        app.add_middleware(SPAMiddleware)
    else:
        app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

    return app


app = create_app()
