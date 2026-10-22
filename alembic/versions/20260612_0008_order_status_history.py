"""add new order statuses and history table

Revision ID: 20260612_0008
Revises: 20260612_0007
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa

revision = "20260612_0008"
down_revision = "20260612_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Convert status column to varchar
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR(20) USING status::text")

    # 2. Drop old enum
    op.execute("DROP TYPE IF EXISTS orderstatus")

    # 3. Normalize to lowercase + migrate old values
    op.execute("UPDATE orders SET status = LOWER(status)")
    op.execute("UPDATE orders SET status = 'confirmed' WHERE status = 'paid'")
    op.execute("UPDATE orders SET status = 'assembling' WHERE status = 'processing'")
    op.execute("UPDATE orders SET status = 'delivering' WHERE status = 'shipped'")

    # 4. Create new enum
    op.execute("CREATE TYPE orderstatus AS ENUM ('created','confirmed','assembling','delivering','delivered','completed','cancelled')")

    # 5. Convert back to enum
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus")

    # 6. Create history table
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("old_status", sa.String(20), nullable=True),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("order_status_history")
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR(20) USING status::text")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("UPDATE orders SET status = 'paid' WHERE status = 'confirmed'")
    op.execute("UPDATE orders SET status = 'processing' WHERE status = 'assembling'")
    op.execute("UPDATE orders SET status = 'shipped' WHERE status = 'delivering'")
    op.execute("CREATE TYPE orderstatus AS ENUM ('created','paid','processing','shipped','completed','cancelled')")
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus")
