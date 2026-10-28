import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from app.products.router import router as products_router
from app.auth.router import router as auth_router
from app.cashier import models as _cashier_models  # noqa: F401
from app.cashier.router import router as cashier_router
from app.cms.models import PageStatus
from app.cms.router import router as cms_router
from app.cms.service import NewsService, PageService
from app.core.bootstrap import bootstrap_first_admin
from app.core.config import settings
from app.db.session import SessionLocal
from app.delivery import models as _delivery_models  # noqa: F401
from app.delivery.router import router as delivery_router
from app.inventory.router import router as inventory_router
from app.orders.router import router as orders_router
from app.products.service import ProductService
from app.promos import models as _promos_models  # noqa: F401
from app.promos.router import router as promos_router
from app.reviews import models as _reviews_models  # noqa: F401
from app.reviews.router import router as reviews_router
from app.telegram.router import router as telegram_router
from app.users.router import router as users_router
from app.core.constants import UPLOAD_DIR

# --- Docs directory resolution ---
_docs_candidates = [
    Path(__file__).resolve().parent.parent / "docs",
    Path.cwd() / "docs",
    Path("/code/docs"),
]
DOCS_DIR = next((d for d in _docs_candidates if d.is_dir()), _docs_candidates[0])

# --- Vue SPA dist directory ---
DIST_DIR = Path(__file__).resolve().parent / "static" / "dist"

# Cache index.html at import time if dist exists
_cached_index_html: str | None = None
if DIST_DIR.is_dir():
    _index_path = DIST_DIR / "index.html"
    if _index_path.is_file():
        with open(_index_path, "r", encoding="utf-8") as _f:
            _cached_index_html = _f.read()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    settings.validate_secret_key()
    db = SessionLocal()
    try:
        bootstrap_first_admin(db)
    finally:
        db.close()
    yield
    # Shutdown (здесь можно добавить очистку при необходимости)


def create_app() -> FastAPI:
    app = FastAPI(
        title="BuildShop API",
        description="Modular monolith backend for a construction materials store.",
        version="2.0.0",
        lifespan=lifespan,  # ✅ замена deprecated @app.on_event("startup")
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
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
    @app.get("/api/guide/{lang}/{filename}", include_in_schema=False)
    def get_doc(lang: str, filename: str) -> Response:
        if lang not in ("tj", "ru", "en"):
            return Response(content="Language not found", status_code=404)
        safe_name = Path(filename).name
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        filepath = DOCS_DIR / lang / safe_name
        
        # ✅ Security: ensure resolved path stays inside DOCS_DIR/lang
        try:
            resolved = filepath.resolve()
            base = (DOCS_DIR / lang).resolve()
            if not str(resolved).startswith(str(base)):
                return Response(content="Invalid path", status_code=403)
        except (OSError, ValueError):
            return Response(content="Invalid path", status_code=403)
        
        if not filepath.is_file():
            return Response(content="Document not found", status_code=404)
        content = filepath.read_text(encoding="utf-8")
        return Response(content=content, media_type="text/plain; charset=utf-8")

    # --- Sitemap ---
    @app.get("/sitemap.xml", include_in_schema=False)
    def sitemap_xml() -> Response:
        db = SessionLocal()
        try:
            pages = PageService(db).list_pages(status=PageStatus.PUBLISHED)
            news = NewsService(db).list_news(status=PageStatus.PUBLISHED, limit=200)
            products = ProductService(db).list_products(limit=500)
            urls = ["/", "/pages/products.html", "/pages/categories.html", "/pages/news.html"]
            urls.extend(f"/pages/page.html?slug={p.slug}" for p in pages if getattr(p, "robots_index", True))
            urls.extend(f"/pages/news.html?slug={n.slug}" for n in news)
            urls.extend(f"/pages/product.html?id={p.id}" for p in products if getattr(p, "robots_index", True))
            base = settings.site_url.rstrip("/")
            lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            ]
            for url in urls:
                loc = url if url.startswith("http") else f"{base}{url}"
                lines.append(f"  <url><loc>{loc}</loc></url>")
            lines.append("</urlset>")
            return Response(content="\n".join(lines) + "\n", media_type="application/xml")
        finally:
            db.close()

    # --- Static files: uploads ---
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # --- Vue SPA or legacy static ---
    if DIST_DIR.is_dir() and _cached_index_html is not None:
        app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="vue-assets")

        SKIP_PREFIXES = ("/api/", "/docs", "/redoc", "/openapi.json", "/assets/", "/uploads/", "/sitemap.xml")
        old_static = Path(__file__).resolve().parent / "static"

        class SPAMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: StarletteRequest, call_next):
                response = await call_next(request)
                path = request.url.path

                if response.status_code != 404:
                    return response
                if any(path.startswith(p) for p in SKIP_PREFIXES):
                    return response

                # ✅ Security: prevent directory traversal
                relative = path.lstrip("/")
                if not relative:
                    return Response(content=_cached_index_html, media_type="text/html")

                try:
                    file_path = (old_static / relative).resolve()
                    # Ensure resolved path is strictly inside old_static
                    if not str(file_path).startswith(str(old_static.resolve())):
                        return Response(content=_cached_index_html, media_type="text/html")
                except (OSError, ValueError):
                    return Response(content=_cached_index_html, media_type="text/html")

                if file_path.is_file():
                    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
                    return Response(content=file_path.read_bytes(), media_type=mime)

                return Response(content=_cached_index_html, media_type="text/html")

        app.add_middleware(SPAMiddleware)
    else:
        static_dir = Path(__file__).resolve().parent / "static"
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
