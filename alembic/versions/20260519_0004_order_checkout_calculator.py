"""Order checkout fields and product material calculator columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260519_0004"
down_revision: str | None = "20260519_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column("orders", sa.Column("comment", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("delivery_method", sa.String(length=20), server_default="pickup", nullable=False))
    op.add_column("products", sa.Column("coverage_per_unit_m2", sa.Numeric(10, 4), nullable=True))
    op.add_column("products", sa.Column("units_per_pack", sa.Numeric(10, 2), server_default="1", nullable=False))
    op.add_column("products", sa.Column("calc_waste_percent", sa.Numeric(5, 2), server_default="10", nullable=False))


def downgrade() -> None:
    op.drop_column("products", "calc_waste_percent")
    op.drop_column("products", "units_per_pack")
    op.drop_column("products", "coverage_per_unit_m2")
    op.drop_column("orders", "delivery_method")
    op.drop_column("orders", "comment")
    op.drop_column("orders", "phone")
