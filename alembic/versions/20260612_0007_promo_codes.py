from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260612_0007"
down_revision: str | None = "20260612_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if not inspector.has_table("promo_codes"):
        op.create_table(
            "promo_codes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("code", sa.String(50), unique=True, index=True, nullable=False),
            sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("discount_amount", sa.Numeric(12, 2), nullable=True),
            sa.Column("min_order_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
            sa.Column("max_discount", sa.Numeric(12, 2), nullable=True),
            sa.Column("usage_limit", sa.Integer(), nullable=True),
            sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not inspector.has_table("promo_usages"):  # ✅ добавить проверку
        op.create_table(
            "promo_usages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("promo_id", sa.Integer(), sa.ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("discount_applied", sa.Numeric(12, 2), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("promo_usages")
    op.drop_table("promo_codes")
