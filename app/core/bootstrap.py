from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.users.models import User, UserRole
from app.users.repository import UserRepository


def bootstrap_first_admin(db: Session) -> None:
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
