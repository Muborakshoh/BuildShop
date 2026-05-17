"""CMS repository — database queries."""

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session, joinedload

from app.cms.models import MenuItem, MenuLocation, News, Page, PageBlock, PageStatus, SiteSetting


class PageRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, status: PageStatus | None = None):
        q = self.db.query(Page)
        if status:
            q = q.filter(Page.status == status)
        return q.order_by(Page.sort_order, Page.id).all()

    def get_by_id(self, page_id: int) -> Page | None:
        return (
            self.db.query(Page)
            .options(joinedload(Page.blocks))
            .filter(Page.id == page_id)
            .first()
        )

    def get_by_slug(self, slug: str) -> Page | None:
        return (
            self.db.query(Page)
            .options(joinedload(Page.blocks))
            .filter(Page.slug == slug)
            .first()
        )

    def slug_exists(self, slug: str, exclude_id: int | None = None) -> bool:
        q = self.db.query(Page.id).filter(Page.slug == slug)
        if exclude_id:
            q = q.filter(Page.id != exclude_id)
        return q.first() is not None

    def create(self, page: Page) -> Page:
        self.db.add(page)
        self.db.flush()
        return page

    def delete(self, page: Page) -> None:
        self.db.delete(page)


class PageBlockRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, block_id: int) -> PageBlock | None:
        return self.db.query(PageBlock).filter(PageBlock.id == block_id).first()

    def list_by_page(self, page_id: int):
        return (
            self.db.query(PageBlock)
            .filter(PageBlock.page_id == page_id)
            .order_by(PageBlock.sort_order)
            .all()
        )

    def create(self, block: PageBlock) -> PageBlock:
        self.db.add(block)
        self.db.flush()
        return block

    def delete(self, block: PageBlock) -> None:
        self.db.delete(block)


class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, status: PageStatus | None = None, limit: int = 50, offset: int = 0):
        q = self.db.query(News)
        if status:
            q = q.filter(News.status == status)
        return q.order_by(News.pinned.desc(), News.created_at.desc()).offset(offset).limit(limit).all()

    def count(self, status: PageStatus | None = None) -> int:
        q = self.db.query(sa_func.count(News.id))
        if status:
            q = q.filter(News.status == status)
        return q.scalar() or 0

    def get_by_id(self, news_id: int) -> News | None:
        return self.db.query(News).filter(News.id == news_id).first()

    def get_by_slug(self, slug: str) -> News | None:
        return self.db.query(News).filter(News.slug == slug).first()

    def slug_exists(self, slug: str, exclude_id: int | None = None) -> bool:
        q = self.db.query(News.id).filter(News.slug == slug)
        if exclude_id:
            q = q.filter(News.id != exclude_id)
        return q.first() is not None

    def create(self, news: News) -> News:
        self.db.add(news)
        self.db.flush()
        return news

    def delete(self, news: News) -> None:
        self.db.delete(news)


class MenuItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_location(self, location: MenuLocation, active_only: bool = True):
        q = self.db.query(MenuItem).filter(MenuItem.location == location, MenuItem.parent_id.is_(None))
        if active_only:
            q = q.filter(MenuItem.is_active.is_(True))
        return q.order_by(MenuItem.sort_order).all()

    def list_all(self):
        return self.db.query(MenuItem).order_by(MenuItem.location, MenuItem.sort_order).all()

    def get_by_id(self, item_id: int) -> MenuItem | None:
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def create(self, item: MenuItem) -> MenuItem:
        self.db.add(item)
        self.db.flush()
        return item

    def delete(self, item: MenuItem) -> None:
        self.db.delete(item)


class SiteSettingRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, group: str | None = None):
        q = self.db.query(SiteSetting)
        if group:
            q = q.filter(SiteSetting.group_name == group)
        return q.order_by(SiteSetting.group_name, SiteSetting.key).all()

    def get_by_key(self, key: str) -> SiteSetting | None:
        return self.db.query(SiteSetting).filter(SiteSetting.key == key).first()

    def upsert(self, key: str, value: str | None, value_type: str = "text",
               label: str | None = None, group_name: str = "general") -> SiteSetting:
        existing = self.get_by_key(key)
        if existing:
            existing.value = value
            existing.value_type = value_type
            if label is not None:
                existing.label = label
            if group_name:
                existing.group_name = group_name
            self.db.flush()
            return existing
        s = SiteSetting(key=key, value=value, value_type=value_type, label=label, group_name=group_name)
        self.db.add(s)
        self.db.flush()
        return s

    def delete(self, setting: SiteSetting) -> None:
        self.db.delete(setting)
