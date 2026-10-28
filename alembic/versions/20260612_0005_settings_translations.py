"""Add translations column to cms_site_settings."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect  # ✅ добавить

revision: str = "20260612_0005"
down_revision: str | None = "20260519_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(bind, table, column):
    inspector = inspect(bind)
    if not inspector.has_table(table):
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "cms_site_settings", "translations"):
        return
    with op.batch_alter_table("cms_site_settings") as batch_op:
        batch_op.add_column(sa.Column("translations", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("cms_site_settings") as batch_op:
        batch_op.drop_column("translations")
