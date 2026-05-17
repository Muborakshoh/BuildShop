"""Create local development schema.

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14
"""

from alembic import op
from sqlalchemy import inspect, text

from app.db.session import Base

from app.cashier import models as _cashier_models  # noqa: F401
from app.cms import models as _cms_models  # noqa: F401
from app.inventory import models as _inventory_models  # noqa: F401
from app.orders import models as _orders_models  # noqa: F401
from app.products import models as _products_models  # noqa: F401
from app.users import models as _users_models  # noqa: F401

revision = "20260514_0001"
down_revision = None
branch_labels = None
depends_on = None


def _add_column_if_missing(table: str, column: str, ddl: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table):
        return
    existing = {c["name"] for c in inspector.get_columns(table)}
    if column not in existing:
        bind.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    # Keep old local Docker volumes usable when they were created before Alembic.
    _add_column_if_missing("products", "unit", "unit VARCHAR(20) NOT NULL DEFAULT 'шт'")
    _add_column_if_missing("products", "volume", "volume VARCHAR(50)")
    _add_column_if_missing("products", "translations", "translations TEXT")
    _add_column_if_missing("categories", "image_url", "image_url VARCHAR(500)")
    _add_column_if_missing("categories", "translations", "translations TEXT")
    _add_column_if_missing("cms_pages", "translations", "translations TEXT")
    _add_column_if_missing("cms_news", "translations", "translations TEXT")


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
