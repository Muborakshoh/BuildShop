"""CMS router — admin CRUD + public read endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.cms.models import MenuLocation, PageStatus
from app.cms.schemas import (
    MenuItemCreate, MenuItemOut, MenuItemUpdate,
    NewsCreate, NewsListItem, NewsOut, NewsUpdate,
    PageBlockIn, PageBlockOut,
    PageCreate, PageDetail, PageListItem, PageUpdate,
    SiteSettingBulkUpdate, SiteSettingIn, SiteSettingOut,
)
from app.cms.service import MenuService, NewsService, PageService, SettingsService
from app.core.dependencies import get_current_user, get_db, require_admin
from app.users.models import User

router = APIRouter(prefix="/api/cms", tags=["CMS"])


# ═══════════════════════════════════════════════════════════════════
# PUBLIC endpoints (no auth required)
# ═══════════════════════════════════════════════════════════════════

@router.get("/pages/public", response_model=list[PageListItem])
def public_list_pages(db: Session = Depends(get_db)):
    """List published pages for navigation."""
    svc = PageService(db)
    pages = svc.list_pages(status=PageStatus.PUBLISHED)
    for p in pages:
        p.blocks_count = len(p.blocks)
    return pages


@router.get("/pages/public/by-slug/{slug}", response_model=PageDetail)
def public_get_page_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a published page by slug."""
    svc = PageService(db)
    page = svc.get_page_by_slug(slug)
    if page.status != PageStatus.PUBLISHED:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.get("/news/public", response_model=list[NewsListItem])
def public_list_news(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List published news."""
    svc = NewsService(db)
    return svc.list_news(status=PageStatus.PUBLISHED, limit=limit, offset=offset)


@router.get("/news/public/by-slug/{slug}", response_model=NewsOut)
def public_get_news_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a published news article by slug."""
    svc = NewsService(db)
    news = svc.get_news_by_slug(slug)
    if news.status != PageStatus.PUBLISHED:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.get("/menus/public/{location}", response_model=list[MenuItemOut])
def public_get_menu(location: MenuLocation, db: Session = Depends(get_db)):
    """Get active menu items by location."""
    svc = MenuService(db)
    return svc.list_by_location(location, active_only=True)


@router.get("/settings/public", response_model=list[SiteSettingOut])
def public_get_settings(
    group: str | None = None,
    db: Session = Depends(get_db),
):
    """Get site settings (public, read-only)."""
    svc = SettingsService(db)
    return svc.list_all(group)


# ═══════════════════════════════════════════════════════════════════
# ADMIN endpoints (require admin role)
# ═══════════════════════════════════════════════════════════════════

# ── Pages ────────────────────────────────────────────────────────

@router.get("/pages", response_model=list[PageListItem])
def admin_list_pages(
    status: PageStatus | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = PageService(db)
    pages = svc.list_pages(status)
    for p in pages:
        p.blocks_count = len(p.blocks)
    return pages


@router.get("/pages/{page_id}", response_model=PageDetail)
def admin_get_page(
    page_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).get_page(page_id)


@router.post("/pages", response_model=PageDetail, status_code=201)
def admin_create_page(
    data: PageCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).create_page(data, admin.id)


@router.patch("/pages/{page_id}", response_model=PageDetail)
def admin_update_page(
    page_id: int,
    data: PageUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).update_page(page_id, data)


@router.delete("/pages/{page_id}", status_code=204)
def admin_delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    PageService(db).delete_page(page_id)


# ── Blocks ───────────────────────────────────────────────────────

@router.post("/pages/{page_id}/blocks", response_model=PageBlockOut, status_code=201)
def admin_add_block(
    page_id: int,
    data: PageBlockIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).add_block(page_id, data)


@router.put("/blocks/{block_id}", response_model=PageBlockOut)
def admin_update_block(
    block_id: int,
    data: PageBlockIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).update_block(block_id, data)


@router.delete("/blocks/{block_id}", status_code=204)
def admin_delete_block(
    block_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    PageService(db).delete_block(block_id)


@router.post("/pages/{page_id}/blocks/reorder", response_model=list[PageBlockOut])
def admin_reorder_blocks(
    page_id: int,
    block_ids: list[int],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).reorder_blocks(page_id, block_ids)


# ── News ─────────────────────────────────────────────────────────

@router.get("/news", response_model=list[NewsListItem])
def admin_list_news(
    status: PageStatus | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return NewsService(db).list_news(status, limit, offset)


@router.get("/news/{news_id}", response_model=NewsOut)
def admin_get_news(
    news_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return NewsService(db).get_news(news_id)


@router.post("/news", response_model=NewsOut, status_code=201)
def admin_create_news(
    data: NewsCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return NewsService(db).create_news(data, admin.id)


@router.patch("/news/{news_id}", response_model=NewsOut)
def admin_update_news(
    news_id: int,
    data: NewsUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return NewsService(db).update_news(news_id, data)


@router.delete("/news/{news_id}", status_code=204)
def admin_delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    NewsService(db).delete_news(news_id)


# ── Menu Items ───────────────────────────────────────────────────

@router.get("/menus", response_model=list[MenuItemOut])
def admin_list_menus(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return MenuService(db).list_all()


@router.post("/menus", response_model=MenuItemOut, status_code=201)
def admin_create_menu_item(
    data: MenuItemCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return MenuService(db).create_item(data)


@router.patch("/menus/{item_id}", response_model=MenuItemOut)
def admin_update_menu_item(
    item_id: int,
    data: MenuItemUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return MenuService(db).update_item(item_id, data)


@router.delete("/menus/{item_id}", status_code=204)
def admin_delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    MenuService(db).delete_item(item_id)


# ── Site Settings ────────────────────────────────────────────────

@router.get("/settings", response_model=list[SiteSettingOut])
def admin_list_settings(
    group: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return SettingsService(db).list_all(group)


@router.post("/settings", response_model=SiteSettingOut, status_code=201)
def admin_upsert_setting(
    data: SiteSettingIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return SettingsService(db).upsert(data)


@router.post("/settings/bulk", response_model=list[SiteSettingOut])
def admin_bulk_upsert_settings(
    data: SiteSettingBulkUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return SettingsService(db).bulk_upsert(data.settings)


@router.delete("/settings/{key}", status_code=204)
def admin_delete_setting(
    key: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    SettingsService(db).delete(key)
