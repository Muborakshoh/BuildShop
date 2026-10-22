from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.users.models import User, UserRole
from app.users.repository import UserRepository


def _ensure_columns(db: Session) -> None:
    """Ensure new columns exist (safety net if migration hasn't run yet)."""
    cols = [
        ("users", "phone", "phone VARCHAR(20)"),
        ("users", "telegram_id", "telegram_id INTEGER UNIQUE"),
        ("users", "telegram_username", "telegram_username VARCHAR(100)"),
        ("orders", "payment_method", "payment_method VARCHAR(30) NOT NULL DEFAULT 'cash'"),
        ("orders", "delivery_zone_id", "delivery_zone_id INTEGER"),
        ("orders", "delivery_price", "delivery_price NUMERIC(10,2) NOT NULL DEFAULT 0"),
        ("order_items", "product_name", "product_name VARCHAR(255)"),
        ("cash_transaction_items", "product_name", "product_name VARCHAR(255)"),
    ]
    for table, col, ddl in cols:
        try:
            result = db.execute(text(
                "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
            ), {"t": table, "c": col})
            if not result.fetchone():
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
                db.commit()
        except Exception:
            db.rollback()

    # Ensure delivery_zones table
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS delivery_zones (
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
        result = db.execute(text("SELECT COUNT(*) FROM delivery_zones"))
        if result.scalar() == 0:
            db.execute(text("""
                INSERT INTO delivery_zones (name, price, min_order_for_free, estimated_days, sort_order) VALUES
                ('Душанбе (марказ)', 20, 500, '1 рӯз', 1),
                ('Душанбе (канорҳо)', 35, 800, '1-2 рӯз', 2),
                ('Ноҳияҳои наздик', 60, 1500, '2-3 рӯз', 3),
                ('Байни шаҳрӣ', 120, 3000, '3-5 рӯз', 4)
            """))
        db.commit()
    except Exception:
        db.rollback()


def bootstrap_first_admin(db: Session) -> None:
    _ensure_columns(db)
    ensure_user_roles(db)
    if not settings.first_admin_email or not settings.first_admin_password:
        return
    repo = UserRepository(db)
    existing = repo.get_by_email(settings.first_admin_email)
    if existing:
        return
    admin = User(
        email=settings.first_admin_email,
        full_name=settings.first_admin_name,
        hashed_password=hash_password(settings.first_admin_password),
        role=UserRole.ADMIN,
    )
    repo.create(admin)


def ensure_user_roles(db: Session) -> None:
    for role in ("MANAGER", "SELLER", "BUYER"):
        try:
            db.execute(text(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{role}'"))
            db.commit()
        except Exception:
            db.rollback()
