"""Change telegram_id from Integer to BigInteger for large Telegram IDs

Revision ID: 20260620_0011
Revises: 20260619_0010
"""
from alembic import op
import sqlalchemy as sa

revision = "20260620_0011"
down_revision = "20260619_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
