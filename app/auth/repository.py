from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import EmailVerification
from app.users.models import User
from app.users.repository import UserRepository


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def get_user_by_email(self, email: str) -> User | None:
        return self.users.get_by_email(email)

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.users.get_by_id(user_id)

    def create_email_verification(self, verification: EmailVerification) -> EmailVerification:
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification

    def latest_email_verification(self, email: str, purpose: str = "registration") -> EmailVerification | None:
        stmt = (
            select(EmailVerification)
            .where(
                EmailVerification.email == email,
                EmailVerification.purpose == purpose,
                EmailVerification.consumed_at.is_(None),
                EmailVerification.expires_at > datetime.now(UTC),
            )
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
