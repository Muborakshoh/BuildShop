"""CMS router — admin CRUD + public read endpoints."""

from fastapi import BackgroundTasks, APIRouter, Depends, Query, Response, UploadFile, Form, Request, HTTPException
from sqlalchemy.orm import Session

from app.cms.models import MenuLocation, PageStatus
from app.cms.schemas import (
    AiProductCopyIn, AiTranslateIn, AuditLogOut, CalculatorIn, ContactIn, PublicStatsOut,
    MenuItemCreate, MenuItemOut, MenuItemUpdate,
    MediaAssetOut, MediaAssetUpdate,
    NewsCreate, NewsListItem, NewsOut, NewsUpdate,
    PageBlockIn, PageBlockOut,
    PageCreate, PageDetail, PageListItem, PageUpdate,
    PageVersionDetail, PageVersionOut,
    SiteSettingBulkUpdate, SiteSettingIn, SiteSettingOut, TrackEventIn,
)
from app.cms.service import GrowthService, MediaService, MenuService, NewsService, PageService, SettingsService
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db, require_admin
from app.core.rate_limit import rate_limit
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
    if group and group not in settings.public_setting_groups:
        raise HTTPException(status_code=404, detail="Settings group not found")
    svc = SettingsService(db)
    items = svc.list_all(group)
    if not group:
        items = [item for item in items if item.group_name in settings.public_setting_groups]
    return items


@router.get("/stats/public", response_model=PublicStatsOut)
def public_stats(db: Session = Depends(get_db)) -> dict:
    return GrowthService(db).public_stats()


@router.post("/contact", status_code=204)
def public_contact(data: ContactIn, request: Request, db: Session = Depends(get_db)) -> None:
    rate_limit(request, key_prefix="cms:contact", max_calls=5, window_seconds=3600)
    GrowthService(db).send_contact_message(data.email, data.subject, data.message)


@router.post("/analytics/track", status_code=204)
def public_track_event(data: TrackEventIn, request: Request, db: Session = Depends(get_db)) -> None:
    rate_limit(request, key_prefix="cms:analytics", max_calls=120, window_seconds=60)
    GrowthService(db).track_view(data.path, data.product_id, data.page_id, data.search_query)


@router.post("/calculators/material/public")
def public_material_calculator(data: CalculatorIn, db: Session = Depends(get_db)) -> dict:
    return GrowthService(db).material_calculator(data.area_m2, data.coverage_per_unit_m2, data.waste_percent, data.units_per_pack)


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
    return PageService(db).update_page(page_id, data, admin.id)


@router.delete("/pages/{page_id}", status_code=204)
def admin_delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    PageService(db).delete_page(page_id, admin.id)


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


@router.put("/pages/{page_id}/blocks", response_model=list[PageBlockOut])
def admin_replace_blocks(
    page_id: int,
    data: list[PageBlockIn],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).replace_blocks(page_id, data, admin.id)


@router.get("/pages/{page_id}/versions", response_model=list[PageVersionOut])
def admin_list_page_versions(
    page_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).list_versions(page_id)


@router.get("/pages/versions/{version_id}", response_model=PageVersionDetail)
def admin_get_page_version(
    version_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).get_version(version_id)


@router.post("/pages/{page_id}/versions/{version_id}/restore", response_model=PageDetail)
def admin_restore_page_version(
    page_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return PageService(db).restore_version(page_id, version_id, admin.id)



@router.put("/pages/{page_id}/blocks/bulk", response_model=list[PageBlockOut])
def admin_replace_all_blocks(
    page_id: int,
    blocks: list[PageBlockIn],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Replace ALL blocks on a page atomically (single transaction)."""
    return PageService(db).replace_blocks(page_id, blocks)

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    article = NewsService(db).create_news(data, admin.id)
    # Broadcast to Telegram users if published
    if getattr(data, 'status', None) == 'published':
        background_tasks.add_task(_broadcast_news_tg, article.title, article.summary, article.slug)
    return article


@router.patch("/news/{news_id}", response_model=NewsOut)
def admin_update_news(
    news_id: int,
    data: NewsUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    article = NewsService(db).update_news(news_id, data)
    if getattr(data, 'status', None) == 'published':
        background_tasks.add_task(_broadcast_news_tg, article.title, article.summary, article.slug)
    return article


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


# ── Growth CMS ──────────────────────────────────────────────────

@router.get("/media", response_model=list[MediaAssetOut])
def admin_list_media(
    search: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = MediaService(db)
    items = svc.list_assets(search)
    output = []
    for item in items:
        item.used_count = svc.used_count(item)
        output.append(item)
    return output


@router.post("/media", response_model=MediaAssetOut, status_code=201)
async def admin_upload_media(
    file: UploadFile,
    alt_text: str | None = Form(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    asset = MediaService(db).save_asset(file.filename or "media.png", file.content_type or "", await file.read(), alt_text, admin.id)
    asset.used_count = 0
    return asset


@router.patch("/media/{asset_id}", response_model=MediaAssetOut)
def admin_update_media(
    asset_id: int,
    data: MediaAssetUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    asset = MediaService(db).update_asset(asset_id, data.alt_text, admin.id)
    asset.used_count = MediaService(db).used_count(asset)
    return asset


@router.delete("/media/{asset_id}", status_code=204)
def admin_delete_media(
    asset_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    MediaService(db).delete_asset(asset_id, admin.id)


@router.post("/ai/product-copy")
def admin_ai_product_copy(
    data: AiProductCopyIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return GrowthService(db).generate_product_copy(data.name, data.category, data.unit, data.volume)


@router.post("/ai/translate")
def admin_ai_translate(
    data: AiTranslateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return GrowthService(db).translate_text(data.text, data.field)


@router.get("/audit", response_model=list[AuditLogOut])
def admin_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return GrowthService(db).audit_logs(limit)


@router.get("/reports/dashboard")
def admin_reports_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return GrowthService(db).dashboard()


@router.post("/calculators/material")
def admin_material_calculator(
    data: CalculatorIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return GrowthService(db).material_calculator(data.area_m2, data.coverage_per_unit_m2, data.waste_percent, data.units_per_pack)
