"""CMS Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.cms.models import BlockType, MenuLocation, PageStatus
from app.core.translations import translations_validator


# ── Page ─────────────────────────────────────────────────────────

class PageBlockIn(BaseModel):
    block_type: BlockType
    content: str | None = None
    image_url: str | None = None
    settings_json: str | None = None
    sort_order: int = 0


class PageBlockOut(PageBlockIn):
    id: int
    page_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(default="", max_length=280)
    description: str | None = None
    status: PageStatus = PageStatus.DRAFT
    sort_order: int = 0
    show_in_nav: bool = False
    meta_title: str | None = None
    meta_description: str | None = None
    og_image: str | None = None
    robots_index: bool = True
    canonical_url: str | None = None
    blocks: list[PageBlockIn] = Field(default_factory=list)
    translations: str | None = None

    _validate_translations = translations_validator("translations")


class PageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = None
    description: str | None = None
    status: PageStatus | None = None
    sort_order: int | None = None
    show_in_nav: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    og_image: str | None = None
    robots_index: bool | None = None
    canonical_url: str | None = None
    translations: str | None = None

    _validate_translations = translations_validator("translations")


class PageListItem(BaseModel):
    id: int
    title: str
    slug: str
    status: PageStatus
    sort_order: int
    show_in_nav: bool
    created_at: datetime
    updated_at: datetime
    blocks_count: int = 0
    translations: str | None = None

    class Config:
        from_attributes = True


class PageDetail(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None
    status: PageStatus
    sort_order: int
    show_in_nav: bool
    meta_title: str | None
    meta_description: str | None
    og_image: str | None = None
    robots_index: bool = True
    canonical_url: str | None = None
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    blocks: list[PageBlockOut] = []
    translations: str | None = None

    class Config:
        from_attributes = True


# ── News ─────────────────────────────────────────────────────────

class NewsCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(default="", max_length=280)
    summary: str | None = None
    content: str = Field(min_length=1)
    image_url: str | None = None
    status: PageStatus = PageStatus.DRAFT
    pinned: bool = False
    translations: str | None = None

    _validate_translations = translations_validator("translations")


class NewsUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = None
    summary: str | None = None
    content: str | None = None
    image_url: str | None = None
    status: PageStatus | None = None
    pinned: bool | None = None
    translations: str | None = None

    _validate_translations = translations_validator("translations")


class NewsOut(BaseModel):
    id: int
    title: str
    slug: str
    summary: str | None
    content: str
    image_url: str | None
    status: PageStatus
    pinned: bool
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    translations: str | None = None

    class Config:
        from_attributes = True


class NewsListItem(BaseModel):
    id: int
    title: str
    slug: str
    summary: str | None
    image_url: str | None
    status: PageStatus
    pinned: bool
    created_at: datetime
    translations: str | None = None

    class Config:
        from_attributes = True


# ── Menu ─────────────────────────────────────────────────────────

class MenuItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=500)
    location: MenuLocation
    parent_id: int | None = None
    sort_order: int = 0
    is_active: bool = True
    open_new_tab: bool = False
    icon: str | None = None


class MenuItemUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=120)
    url: str | None = None
    location: MenuLocation | None = None
    parent_id: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    open_new_tab: bool | None = None
    icon: str | None = None


class MenuItemOut(BaseModel):
    id: int
    label: str
    url: str
    location: MenuLocation
    parent_id: int | None
    sort_order: int
    is_active: bool
    open_new_tab: bool
    icon: str | None
    children: list[MenuItemOut] = []

    class Config:
        from_attributes = True


# ── Site Settings ────────────────────────────────────────────────

class SiteSettingIn(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str | None = None
    value_type: str = "text"
    label: str | None = None
    group_name: str = "general"
    translations: str | None = None


class SiteSettingOut(BaseModel):
    id: int
    key: str
    value: str | None
    value_type: str
    label: str | None
    group_name: str
    translations: str | None = None

    class Config:
        from_attributes = True


class SiteSettingBulkUpdate(BaseModel):
    settings: list[SiteSettingIn]


class PageVersionOut(BaseModel):
    id: int
    page_id: int
    note: str | None
    created_by_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class PageVersionDetail(PageVersionOut):
    snapshot_json: str


class MediaAssetOut(BaseModel):
    id: int
    filename: str
    url: str
    content_type: str
    size_bytes: int
    alt_text: str | None
    width: int | None
    height: int | None
    created_by_id: int | None
    created_at: datetime
    used_count: int = 0

    class Config:
        from_attributes = True


class MediaAssetUpdate(BaseModel):
    alt_text: str | None = None


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TrackEventIn(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    product_id: int | None = None
    page_id: int | None = None
    search_query: str | None = Field(default=None, max_length=255)


class AiProductCopyIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str | None = None
    unit: str | None = None
    volume: str | None = None
    tone: str | None = "professional"


class AiTranslateIn(BaseModel):
    text: str = Field(min_length=1)
    field: str = "description"


class CalculatorIn(BaseModel):
    area_m2: float = Field(gt=0)
    coverage_per_unit_m2: float = Field(gt=0)
    waste_percent: float = Field(default=10, ge=0, le=100)
    units_per_pack: float = Field(default=1, gt=0)


class ContactIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=5000)


class PublicStatsOut(BaseModel):
    products: int
    customers: int
    orders: int
    years_experience: int
