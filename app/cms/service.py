"""CMS service — business logic."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cms.models import MenuItem, News, Page, PageBlock, SiteSetting
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
            return page
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Page with this slug already exists")

    def update_page(self, page_id: int, data: PageUpdate) -> Page:
        page = self.get_page(page_id)
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
            return page
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Slug conflict")

    def delete_page(self, page_id: int) -> None:
        page = self.get_page(page_id)
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
