"""CMS service — business logic."""

import json
import math
import os
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cms.models import AuditLog, BlockType, MediaAsset, MenuItem, News, Page, PageBlock, PageStatus, PageVersion, PageView, SiteSetting
from app.cms.repository import (
    MenuItemRepository,
    NewsRepository,
    PageBlockRepository,
    PageRepository,
    SiteSettingRepository,
)
from app.cms.schemas import (
    MenuItemCreate, MenuItemUpdate,
    NewsCreate, NewsUpdate,
    PageBlockIn,
    PageCreate, PageUpdate,
    SiteSettingIn,
)
from app.core.html_sanitizer import sanitize_html
from app.products.service import generate_slug  # reuse existing slug generator

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
MAX_MEDIA_SIZE = 10 * 1024 * 1024
ALLOWED_MEDIA_TYPES = {
    ".gif": ("image/gif", b"GIF8"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".webp": ("image/webp", b"RIFF"),
}


# ── Helpers ──────────────────────────────────────────────────────

def _unique_slug(slug_base: str, exists_fn, exclude_id: int | None = None) -> str:
    slug = slug_base or "page"
    if not exists_fn(slug, exclude_id):
        return slug
    for i in range(1, 500):
        candidate = f"{slug}-{i}"
        if not exists_fn(candidate, exclude_id):
            return candidate
    return f"{slug}-auto"


def _clean_block_content(data: PageBlockIn) -> str | None:
    if data.block_type.value in {"richtext", "html"}:
        return sanitize_html(data.content)
    return data.content


def log_audit(
    db: Session,
    actor_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: dict | None = None,
) -> AuditLog:
    item = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=json.dumps(details or {}, ensure_ascii=False),
    )
    db.add(item)
    return item


# ── Page Service ─────────────────────────────────────────────────

class PageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PageRepository(db)
        self.block_repo = PageBlockRepository(db)

    def list_pages(self, status=None):
        pages = self.repo.list_all(status)
        for p in pages:
            p.blocks_count = len(p.blocks) if self.db.object_session(p) else 0
        return pages

    def get_page(self, page_id: int) -> Page:
        page = self.repo.get_by_id(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page

    def get_page_by_slug(self, slug: str) -> Page:
        page = self.repo.get_by_slug(slug)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page

    def _snapshot_page(self, page: Page, user_id: int | None, note: str) -> PageVersion:
        snapshot = {
            "page": {
                "title": page.title,
                "slug": page.slug,
                "description": page.description,
                "status": page.status.value if hasattr(page.status, "value") else page.status,
                "sort_order": page.sort_order,
                "show_in_nav": page.show_in_nav,
                "meta_title": page.meta_title,
                "meta_description": page.meta_description,
                "og_image": page.og_image,
                "robots_index": page.robots_index,
                "canonical_url": page.canonical_url,
                "translations": page.translations,
            },
            "blocks": [
                {
                    "block_type": b.block_type.value if hasattr(b.block_type, "value") else b.block_type,
                    "content": b.content,
                    "image_url": b.image_url,
                    "settings_json": b.settings_json,
                    "sort_order": b.sort_order,
                }
                for b in sorted(page.blocks, key=lambda b: b.sort_order)
            ],
        }
        version = PageVersion(
            page_id=page.id,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
            note=note,
            created_by_id=user_id,
        )
        self.db.add(version)
        return version

    def create_page(self, data: PageCreate, user_id: int) -> Page:
        slug = _unique_slug(
            data.slug or generate_slug(data.title),
            self.repo.slug_exists,
        )
        page = Page(
            title=data.title,
            slug=slug,
            description=data.description,
            status=data.status,
            sort_order=data.sort_order,
            show_in_nav=data.show_in_nav,
            meta_title=data.meta_title,
            meta_description=data.meta_description,
            og_image=data.og_image,
            robots_index=data.robots_index,
            canonical_url=data.canonical_url,
            created_by_id=user_id,
            translations=data.translations,
        )
        try:
            self.repo.create(page)
            # Create blocks if provided
            for b in data.blocks:
                block = PageBlock(
                    page_id=page.id,
                    block_type=b.block_type,
                    content=_clean_block_content(b),
                    image_url=b.image_url,
                    settings_json=b.settings_json,
                    sort_order=b.sort_order,
                )
                self.block_repo.create(block)
            self.db.commit()
            self.db.refresh(page)
            log_audit(self.db, user_id, "create", "page", page.id, {"title": page.title})
            self.db.commit()
            return page
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Page with this slug already exists")

    def update_page(self, page_id: int, data: PageUpdate, user_id: int | None = None) -> Page:
        page = self.get_page(page_id)
        self._snapshot_page(page, user_id, "Before page save")
        update_data = data.model_dump(exclude_unset=True)
        if "slug" in update_data and update_data["slug"]:
            update_data["slug"] = _unique_slug(
                update_data["slug"], self.repo.slug_exists, exclude_id=page_id,
            )
        for key, val in update_data.items():
            setattr(page, key, val)
        try:
            self.db.commit()
            self.db.refresh(page)
            log_audit(self.db, user_id, "update", "page", page.id, {"title": page.title})
            self.db.commit()
            return page
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Slug conflict")

    def delete_page(self, page_id: int, user_id: int | None = None) -> None:
        page = self.get_page(page_id)
        self._snapshot_page(page, user_id, "Before page delete")
        log_audit(self.db, user_id, "delete", "page", page.id, {"title": page.title})
        self.repo.delete(page)
        self.db.commit()

    # ── Block operations ──

    def add_block(self, page_id: int, data: PageBlockIn) -> PageBlock:
        self.get_page(page_id)  # ensure page exists
        block = PageBlock(
            page_id=page_id,
            block_type=data.block_type,
            content=_clean_block_content(data),
            image_url=data.image_url,
            settings_json=data.settings_json,
            sort_order=data.sort_order,
        )
        self.block_repo.create(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def update_block(self, block_id: int, data: PageBlockIn) -> PageBlock:
        block = self.block_repo.get_by_id(block_id)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        block.block_type = data.block_type
        block.content = _clean_block_content(data)
        block.image_url = data.image_url
        block.settings_json = data.settings_json
        block.sort_order = data.sort_order
        self.db.commit()
        self.db.refresh(block)
        return block

    def delete_block(self, block_id: int) -> None:
        block = self.block_repo.get_by_id(block_id)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        self.block_repo.delete(block)
        self.db.commit()

    def reorder_blocks(self, page_id: int, block_ids: list[int]) -> list[PageBlock]:
        self.get_page(page_id)
        blocks = self.block_repo.list_by_page(page_id)
        id_map = {b.id: b for b in blocks}
        for i, bid in enumerate(block_ids):
            if bid in id_map:
                id_map[bid].sort_order = i
        self.db.commit()
        return self.block_repo.list_by_page(page_id)

    def replace_blocks(self, page_id: int, items: list[PageBlockIn], user_id: int | None = None) -> list[PageBlock]:
        page = self.get_page(page_id)
        try:
            self._snapshot_page(page, user_id, "Before blocks save")
            for block in self.block_repo.list_by_page(page_id):
                self.block_repo.delete(block)
            for i, data in enumerate(items):
                block = PageBlock(
                    page_id=page_id,
                    block_type=data.block_type,
                    content=_clean_block_content(data),
                    image_url=data.image_url,
                    settings_json=data.settings_json,
                    sort_order=i,
                )
                self.block_repo.create(block)
            log_audit(self.db, user_id, "replace_blocks", "page", page_id, {"blocks": len(items)})
            self.db.commit()
            return self.block_repo.list_by_page(page_id)
        except Exception:
            self.db.rollback()
            raise

    def list_versions(self, page_id: int) -> list[PageVersion]:
        self.get_page(page_id)
        return (
            self.db.query(PageVersion)
            .filter(PageVersion.page_id == page_id)
            .order_by(PageVersion.created_at.desc())
            .all()
        )

    def get_version(self, version_id: int) -> PageVersion:
        version = self.db.get(PageVersion, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        return version

    def restore_version(self, page_id: int, version_id: int, user_id: int | None = None) -> Page:
        page = self.get_page(page_id)
        version = self.get_version(version_id)
        if version.page_id != page_id:
            raise HTTPException(status_code=400, detail="Version belongs to another page")
        self._snapshot_page(page, user_id, "Before version restore")
        snapshot = json.loads(version.snapshot_json)
        for key, value in snapshot["page"].items():
            if key == "status" and value:
                value = PageStatus(value)
            setattr(page, key, value)
        for block in self.block_repo.list_by_page(page_id):
            self.block_repo.delete(block)
        for item in snapshot.get("blocks", []):
            if item.get("block_type"):
                item["block_type"] = BlockType(item["block_type"])
            self.block_repo.create(PageBlock(page_id=page_id, **item))
        log_audit(self.db, user_id, "restore_version", "page", page_id, {"version_id": version_id})
        self.db.commit()
        self.db.refresh(page)
        return page
# ── News Service ─────────────────────────────────────────────────

class NewsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NewsRepository(db)

    def list_news(self, status=None, limit=50, offset=0):
        return self.repo.list_all(status, limit, offset)

    def count_news(self, status=None) -> int:
        return self.repo.count(status)

    def get_news(self, news_id: int) -> News:
        news = self.repo.get_by_id(news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        return news

    def get_news_by_slug(self, slug: str) -> News:
        news = self.repo.get_by_slug(slug)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        return news

    def create_news(self, data: NewsCreate, user_id: int) -> News:
        slug = _unique_slug(
            data.slug or generate_slug(data.title),
            self.repo.slug_exists,
        )
        news = News(
            title=data.title,
            slug=slug,
            summary=data.summary,
            content=sanitize_html(data.content) or "",
            image_url=data.image_url,
            status=data.status,
            pinned=data.pinned,
            created_by_id=user_id,
            translations=data.translations,
        )
        try:
            self.repo.create(news)
            self.db.commit()
            self.db.refresh(news)
            return news
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="News slug conflict")

    def update_news(self, news_id: int, data: NewsUpdate) -> News:
        news = self.get_news(news_id)
        update_data = data.model_dump(exclude_unset=True)
        if "content" in update_data:
            update_data["content"] = sanitize_html(update_data["content"]) or ""
        if "slug" in update_data and update_data["slug"]:
            update_data["slug"] = _unique_slug(
                update_data["slug"], self.repo.slug_exists, exclude_id=news_id,
            )
        for key, val in update_data.items():
            setattr(news, key, val)
        try:
            self.db.commit()
            self.db.refresh(news)
            return news
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Slug conflict")

    def delete_news(self, news_id: int) -> None:
        news = self.get_news(news_id)
        self.repo.delete(news)
        self.db.commit()


# ── Menu Service ─────────────────────────────────────────────────

class MenuService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MenuItemRepository(db)

    def list_all(self):
        return self.repo.list_all()

    def list_by_location(self, location, active_only=True):
        return self.repo.list_by_location(location, active_only)

    def create_item(self, data: MenuItemCreate) -> MenuItem:
        item = MenuItem(**data.model_dump())
        self.repo.create(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, item_id: int, data: MenuItemUpdate) -> MenuItem:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(item, key, val)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item_id: int) -> None:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        self.repo.delete(item)
        self.db.commit()


# ── Settings Service ─────────────────────────────────────────────

class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SiteSettingRepository(db)

    def list_all(self, group: str | None = None):
        return self.repo.list_all(group)

    def get(self, key: str) -> SiteSetting | None:
        return self.repo.get_by_key(key)

    def upsert(self, data: SiteSettingIn) -> SiteSetting:
        s = self.repo.upsert(data.key, data.value, data.value_type, data.label, data.group_name)
        self.db.commit()
        return s

    def bulk_upsert(self, items: list[SiteSettingIn]) -> list[SiteSetting]:
        results = []
        for item in items:
            results.append(self.repo.upsert(item.key, item.value, item.value_type, item.label, item.group_name))
        self.db.commit()
        return results

    def delete(self, key: str) -> None:
        s = self.repo.get_by_key(key)
        if not s:
            raise HTTPException(status_code=404, detail="Setting not found")
        self.repo.delete(s)
        self.db.commit()


class MediaService:
    def __init__(self, db: Session):
        self.db = db

    def list_assets(self, search: str | None = None) -> list[MediaAsset]:
        query = self.db.query(MediaAsset)
        if search:
            like = f"%{search.lower()}%"
            query = query.filter(func.lower(MediaAsset.filename).like(like) | func.lower(MediaAsset.alt_text).like(like))
        return query.order_by(MediaAsset.created_at.desc()).all()

    def used_count(self, asset: MediaAsset) -> int:
        url = asset.url
        count = self.db.query(PageBlock).filter(
            (PageBlock.image_url == url) | (PageBlock.content.contains(url)) | (PageBlock.settings_json.contains(url))
        ).count()
        return count + self.db.query(Page).filter(Page.og_image == url).count() + self.db.query(News).filter(News.image_url == url).count()

    def save_asset(self, filename: str, content_type: str, content: bytes, alt_text: str | None, user_id: int) -> MediaAsset:
        ext = os.path.splitext(filename or "media.png")[1].lower()
        expected = ALLOWED_MEDIA_TYPES.get(ext)
        if not expected:
            raise HTTPException(status_code=400, detail="Unsupported media type")
        expected_content_type, signature = expected
        if content_type != expected_content_type or not content.startswith(signature):
            raise HTTPException(status_code=400, detail="Media content does not match extension")
        if ext == ".webp" and content[8:12] != b"WEBP":
            raise HTTPException(status_code=400, detail="Invalid WebP file")
        if len(content) > MAX_MEDIA_SIZE:
            raise HTTPException(status_code=413, detail="Media file is too large")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        stored = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(UPLOAD_DIR, stored), "wb") as f:
            f.write(content)
        asset = MediaAsset(
            filename=filename or stored,
            url=f"/uploads/{stored}",
            content_type=content_type,
            size_bytes=len(content),
            alt_text=alt_text,
            created_by_id=user_id,
        )
        self.db.add(asset)
        log_audit(self.db, user_id, "upload", "media", None, {"filename": asset.filename})
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update_asset(self, asset_id: int, alt_text: str | None, user_id: int) -> MediaAsset:
        asset = self.db.get(MediaAsset, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Media asset not found")
        asset.alt_text = alt_text
        log_audit(self.db, user_id, "update", "media", asset.id, {"alt_text": alt_text})
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete_asset(self, asset_id: int, user_id: int) -> None:
        asset = self.db.get(MediaAsset, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Media asset not found")
        if self.used_count(asset) > 0:
            raise HTTPException(status_code=409, detail="Media asset is still used")
        path = os.path.join(UPLOAD_DIR, os.path.basename(asset.url))
        if os.path.exists(path):
            os.remove(path)
        log_audit(self.db, user_id, "delete", "media", asset.id, {"filename": asset.filename})
        self.db.delete(asset)
        self.db.commit()


class GrowthService:
    def __init__(self, db: Session):
        self.db = db

    def track_view(self, path: str, product_id: int | None = None, page_id: int | None = None, search_query: str | None = None) -> PageView:
        view = PageView(path=path, product_id=product_id, page_id=page_id, search_query=search_query)
        self.db.add(view)
        self.db.commit()
        return view

    def audit_logs(self, limit: int = 100) -> list[AuditLog]:
        return self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def dashboard(self) -> dict:
        from app.inventory.models import Inventory
        from app.orders.models import OrderItem
        from app.products.models import Product

        popular = (
            self.db.query(Product.id, Product.name, func.coalesce(func.sum(OrderItem.quantity), 0).label("sold"))
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Product.id)
            .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc(), Product.name.asc())
            .limit(10)
            .all()
        )
        searches = (
            self.db.query(PageView.search_query, func.count(PageView.id).label("count"))
            .filter(PageView.search_query.isnot(None), PageView.search_query != "")
            .group_by(PageView.search_query)
            .order_by(func.count(PageView.id).desc())
            .limit(10)
            .all()
        )
        return {
            "page_views": self.db.query(PageView).count(),
            "pages": self.db.query(Page).count(),
            "products": self.db.query(Product).count(),
            "media": self.db.query(MediaAsset).count(),
            "products_without_photo": self.db.query(Product).filter(Product.image_url.is_(None)).count(),
            "products_without_stock": self.db.query(Product).outerjoin(Inventory).filter((Inventory.quantity.is_(None)) | (Inventory.quantity <= 0)).count(),
            "popular_products": [{"id": row.id, "name": row.name, "sold": int(row.sold or 0)} for row in popular],
            "search_queries": [{"query": row.search_query, "count": row.count} for row in searches],
        }

    def generate_product_copy(self, name: str, category: str | None, unit: str | None, volume: str | None) -> dict:
        base = f"{name} барои корҳои сохтмонӣ"
        details = ", ".join(part for part in [category, volume, unit] if part)
        tj = f"{base}. Маҳсулот барои хариди зуд, ҳисобкунии дақиқ ва истифода дар объектҳои сохтмонӣ мувофиқ аст."
        ru = f"{name} для строительных работ. Подходит для быстрого подбора, точного расчета и использования на объекте."
        en = f"{name} for construction work. Suitable for fast selection, accurate estimates and on-site use."
        if details:
            tj += f" Хусусиятҳо: {details}."
            ru += f" Характеристики: {details}."
            en += f" Details: {details}."
        return {
            "description": tj,
            "meta_title": f"{name} | СохтМатериал",
            "meta_description": ru[:500],
            "translations": json.dumps({"description_ru": ru, "description_en": en, "name_ru": name, "name_en": name}, ensure_ascii=False),
        }

    def translate_text(self, text: str, field: str) -> dict:
        return {
            f"{field}_tj": text,
            f"{field}_ru": f"{text} (RU draft)",
            f"{field}_en": f"{text} (EN draft)",
            "note": "Local draft translation. Review before publishing.",
        }

    def material_calculator(self, area_m2: float, coverage_per_unit_m2: float, waste_percent: float, units_per_pack: float) -> dict:
        units = area_m2 / coverage_per_unit_m2 * (1 + waste_percent / 100)
        packs = math.ceil(units / units_per_pack)
        return {
            "area_m2": area_m2,
            "coverage_per_unit_m2": coverage_per_unit_m2,
            "waste_percent": waste_percent,
            "units_needed": math.ceil(units),
            "packs_needed": packs,
        }

    def public_stats(self) -> dict:
        from app.inventory.models import Inventory
        from app.orders.models import Order
        from app.products.models import Product
        from app.users.models import User, UserRole

        customers = (
            self.db.query(User)
            .filter(User.role.in_([UserRole.BUYER, UserRole.USER]))
            .count()
        )
        years_setting = (
            self.db.query(SiteSetting)
            .filter(SiteSetting.key == "years_experience")
            .first()
        )
        years = int(years_setting.value) if years_setting and years_setting.value.isdigit() else 15
        return {
            "products": self.db.query(Product).count(),
            "customers": customers,
            "orders": self.db.query(Order).count(),
            "years_experience": years,
        }

    def send_contact_message(self, email: str, subject: str, message: str) -> None:
        from app.core.email import notify_admin, send_email

        body = f"From: {email}\n\n{message}"
        notify_admin(f"Contact: {subject}", body)
        send_email(email, "СохтМатериал — сообщение получено", "Спасибо! Мы получили ваше сообщение и скоро ответим.")
