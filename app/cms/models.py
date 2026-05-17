"""CMS models — pages, blocks, news, menus, site settings."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── Enums ────────────────────────────────────────────────────────

class PageStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BlockType(str, enum.Enum):
    RICHTEXT = "richtext"
    IMAGE = "image"
    HERO = "hero"
    GALLERY = "gallery"
    VIDEO = "video"
    HTML = "html"
    PRODUCTS = "products"       # embed product grid
    CATEGORIES = "categories"   # embed category grid
    SEPARATOR = "separator"
    CONTACTS = "contacts"
    MAP = "map"


class MenuLocation(str, enum.Enum):
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"


# ── Page (custom section / landing) ──────────────────────────────

class Page(Base):
    __tablename__ = "cms_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PageStatus] = mapped_column(
        Enum(PageStatus), default=PageStatus.DRAFT, nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    show_in_nav: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meta_title: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    translations: Mapped[str | None] = mapped_column(Text)  # JSON multilingual
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    blocks = relationship(
        "PageBlock", back_populates="page",
        cascade="all, delete-orphan", order_by="PageBlock.sort_order",
    )
    created_by = relationship("User", foreign_keys=[created_by_id])


# ── Page Block (content piece inside a page) ────────────────────

class PageBlock(Base):
    __tablename__ = "cms_page_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("cms_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    block_type: Mapped[BlockType] = mapped_column(Enum(BlockType), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)          # rich-text HTML or JSON config
    image_url: Mapped[str | None] = mapped_column(String(500))
    settings_json: Mapped[str | None] = mapped_column(Text)    # JSON for block-specific settings
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    page = relationship("Page", back_populates="blocks")


# ── News / Announcements ────────────────────────────────────────

class News(Base):
    __tablename__ = "cms_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)  # rich-text HTML
    image_url: Mapped[str | None] = mapped_column(String(500))
    translations: Mapped[str | None] = mapped_column(Text)  # JSON multilingual
    status: Mapped[PageStatus] = mapped_column(
        Enum(PageStatus, name="news_status", create_constraint=False),
        default=PageStatus.DRAFT, nullable=False,
    )
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    created_by = relationship("User", foreign_keys=[created_by_id])


# ── Menu Items ───────────────────────────────────────────────────

class MenuItem(Base):
    __tablename__ = "cms_menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[MenuLocation] = mapped_column(Enum(MenuLocation), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("cms_menu_items.id", ondelete="SET NULL"), index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    open_new_tab: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    children = relationship("MenuItem", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("MenuItem", back_populates="children", remote_side=[id])


# ── Site Settings (key-value) ────────────────────────────────────

class SiteSetting(Base):
    __tablename__ = "cms_site_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)  # text, html, json, boolean, number
    label: Mapped[str | None] = mapped_column(String(255))  # human-readable label
    group_name: Mapped[str] = mapped_column(String(80), default="general", nullable=False)
