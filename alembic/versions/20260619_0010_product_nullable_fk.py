"""Add delivery, payment, telegram, product_name denormalization, nullable FK."""

revision = "20260619_0010"
down_revision = "20260612_0009"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect  # ✅ добавить


def _col_exists(conn, table, column):
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def _add_col(conn, table, column, ddl):
    if not _col_exists(conn, table, column):
        conn.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    # 1. User fields
    _add_col(conn, "users", "phone", "phone VARCHAR(20)")
    _add_col(conn, "users", "telegram_id", "telegram_id INTEGER UNIQUE")
    _add_col(conn, "users", "telegram_username", "telegram_username VARCHAR(100)")

    # 2. Order fields
    _add_col(conn, "orders", "payment_method", "payment_method VARCHAR(30) NOT NULL DEFAULT 'cash'")
    _add_col(conn, "orders", "delivery_zone_id", "delivery_zone_id INTEGER")
    _add_col(conn, "orders", "delivery_price", "delivery_price NUMERIC(10,2) NOT NULL DEFAULT 0")

    # 3. product_name denormalization
    for table in ("order_items", "cash_transaction_items"):
        _add_col(conn, table, "product_name", "product_name VARCHAR(255)")
        conn.execute(sa.text(f"""
            UPDATE {table} ti SET product_name = p.name
            FROM products p WHERE ti.product_id = p.id AND ti.product_name IS NULL
        """))

    # 4. Make product_id nullable + ON DELETE SET NULL
    for table in ("order_items", "cash_transaction_items"):
        result = conn.execute(sa.text("""
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = :tbl
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = 'product_id'
        """), {"tbl": table})
        for row in result.fetchall():
            conn.execute(sa.text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{row[0]}"'))

        conn.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN product_id DROP NOT NULL"))
        conn.execute(sa.text(f"""
            ALTER TABLE {table} ADD CONSTRAINT {table}_product_id_fkey
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        """))

    # 5. Delivery zones table — только если не существует
    if not inspector.has_table("delivery_zones"):  # ✅ добавить проверку
        conn.execute(sa.text("""
            CREATE TABLE delivery_zones (
                id SERIAL PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                description TEXT,
                price NUMERIC(10,2) NOT NULL,
                min_order_for_free NUMERIC(10,2),
                estimated_days VARCHAR(20),
                is_active BOOLEAN NOT NULL DEFAULT true,
                sort_order INTEGER NOT NULL DEFAULT 0,
                translations TEXT
            )
        """))

        # Seed defaults
        result = conn.execute(sa.text("SELECT COUNT(*) FROM delivery_zones"))
        if result.scalar() == 0:
            conn.execute(sa.text("""
                INSERT INTO delivery_zones (name, price, min_order_for_free, estimated_days, sort_order) VALUES
                ('Душанбе (марказ)', 20, 500, '1 рӯз', 1),
                ('Душанбе (канорҳо)', 35, 800, '1-2 рӯз', 2),
                ('Ноҳияҳои наздик', 60, 1500, '2-3 рӯз', 3),
                ('Байни шаҳрӣ', 120, 3000, '3-5 рӯз', 4)
            """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS delivery_zones"))
    for table in ("order_items", "cash_transaction_items"):
        conn.execute(sa.text(f"ALTER TABLE {table} DROP COLUMN IF EXISTS product_name"))
        conn.execute(sa.text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_product_id_fkey"))
        conn.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN product_id SET NOT NULL"))
        conn.execute(sa.text(f"""
            ALTER TABLE {table} ADD CONSTRAINT {table}_product_id_fkey
            FOREIGN KEY (product_id) REFERENCES products(id)
        """))
    conn.execute(sa.text("ALTER TABLE orders DROP COLUMN IF EXISTS payment_method"))
    conn.execute(sa.text("ALTER TABLE orders DROP COLUMN IF EXISTS delivery_zone_id"))
    conn.execute(sa.text("ALTER TABLE orders DROP COLUMN IF EXISTS delivery_price"))
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS phone"))
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS telegram_id"))
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS telegram_username"))
