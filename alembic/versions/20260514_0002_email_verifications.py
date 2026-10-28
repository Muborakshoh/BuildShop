from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260514_0002"
down_revision = "20260514_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("email_verifications"):
        return

    op.create_table(
        "email_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=40), server_default="registration", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_verifications_email"), "email_verifications", ["email"], unique=False)
    op.create_index(op.f("ix_email_verifications_id"), "email_verifications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_verifications_id"), table_name="email_verifications")
    op.drop_index(op.f("ix_email_verifications_email"), table_name="email_verifications")
    op.drop_table("email_verifications")
