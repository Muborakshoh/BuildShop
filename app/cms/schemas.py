"""CMS Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.cms.models import BlockType, MenuLocation, PageStatus


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
    blocks: list[PageBlockIn] = Field(default_factory=list)
    translations: str | None = None


class PageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = None
    description: str | None = None
    status: PageStatus | None = None
    sort_order: int | None = None
    show_in_nav: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    translations: str | None = None


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


class NewsUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = None
    summary: str | None = None
    content: str | None = None
    image_url: str | None = None
    status: PageStatus | None = None
    pinned: bool | None = None
    translations: str | None = None


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


class SiteSettingOut(BaseModel):
    id: int
    key: str
    value: str | None
    value_type: str
    label: str | None
    group_name: str

    class Config:
        from_attributes = True


class SiteSettingBulkUpdate(BaseModel):
    settings: list[SiteSettingIn]
