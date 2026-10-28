"""CMS growth features: versions, media, SEO, audit, analytics."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect  # ✅ добавить

revision: str = "20260519_0003"
down_revision: str | None = "20260514_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(bind, table, column):  # ✅ добавить helper
    inspector = inspect(bind)
    if not inspector.has_table(table):
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def _has_table(bind, table):  # ✅ добавить helper
    return inspect(bind).has_table(table)


def upgrade() -> None:
    bind = op.get_bind()

    # --- Columns on cms_pages ---
    if not _has_column(bind, "cms_pages", "og_image"):
        op.add_column("cms_pages", sa.Column("og_image", sa.String(length=500), nullable=True))
    if not _has_column(bind, "cms_pages", "robots_index"):
        op.add_column("cms_pages", sa.Column("robots_index", sa.Boolean(), server_default=sa.true(), nullable=False))
    if not _has_column(bind, "cms_pages", "canonical_url"):
        op.add_column("cms_pages", sa.Column("canonical_url", sa.String(length=500), nullable=True))

    # --- Columns on products ---
    if not _has_column(bind, "products", "meta_title"):
        op.add_column("products", sa.Column("meta_title", sa.String(length=255), nullable=True))
    if not _has_column(bind, "products", "meta_description"):
        op.add_column("products", sa.Column("meta_description", sa.String(length=500), nullable=True))
    if not _has_column(bind, "products", "og_image"):
        op.add_column("products", sa.Column("og_image", sa.String(length=500), nullable=True))
    if not _has_column(bind, "products", "robots_index"):
        op.add_column("products", sa.Column("robots_index", sa.Boolean(), server_default=sa.true(), nullable=False))
    if not _has_column(bind, "products", "canonical_url"):
        op.add_column("products", sa.Column("canonical_url", sa.String(length=500), nullable=True))

    # --- Tables ---
    if not _has_table(bind, "cms_page_versions"):
        op.create_table(
            "cms_page_versions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("page_id", sa.Integer(), nullable=False),
            sa.Column("snapshot_json", sa.Text(), nullable=False),
            sa.Column("note", sa.String(length=255), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["page_id"], ["cms_pages.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_cms_page_versions_id"), "cms_page_versions", ["id"], unique=False)
        op.create_index(op.f("ix_cms_page_versions_page_id"), "cms_page_versions", ["page_id"], unique=False)

    if not _has_table(bind, "cms_media_assets"):
        op.create_table(
            "cms_media_assets",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("url", sa.String(length=500), nullable=False),
            sa.Column("content_type", sa.String(length=120), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("alt_text", sa.String(length=255), nullable=True),
            sa.Column("width", sa.Integer(), nullable=True),
            sa.Column("height", sa.Integer(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_cms_media_assets_id"), "cms_media_assets", ["id"], unique=False)
        op.create_index(op.f("ix_cms_media_assets_url"), "cms_media_assets", ["url"], unique=True)

    if not _has_table(bind, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=120), nullable=False),
            sa.Column("entity_type", sa.String(length=80), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("details_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
        op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)
        op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
        op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
        op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)

    if not _has_table(bind, "page_views"):
        op.create_table(
            "page_views",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("path", sa.String(length=500), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("page_id", sa.Integer(), nullable=True),
            sa.Column("search_query", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["page_id"], ["cms_pages.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_page_views_id"), "page_views", ["id"], unique=False)
        op.create_index(op.f("ix_page_views_path"), "page_views", ["path"], unique=False)
        op.create_index(op.f("ix_page_views_product_id"), "page_views", ["product_id"], unique=False)
        op.create_index(op.f("ix_page_views_page_id"), "page_views", ["page_id"], unique=False)
        op.create_index(op.f("ix_page_views_search_query"), "page_views", ["search_query"], unique=False)


def downgrade() -> None:
    op.drop_table("page_views")
    op.drop_table("audit_logs")
    op.drop_table("cms_media_assets")
    op.drop_table("cms_page_versions")
    for col in ("canonical_url", "robots_index", "og_image", "meta_description", "meta_title"):
        op.drop_column("products", col)
    for col in ("canonical_url", "robots_index", "og_image"):
        op.drop_column("cms_pages", col)
