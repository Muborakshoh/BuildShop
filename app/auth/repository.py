from sqlalchemy.orm import Session

from app.users.models import User
from app.users.repository import UserRepository


class AuthRepository:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def get_user_by_email(self, email: str) -> User | None:
        return self.users.get_by_email(email)

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.users.get_by_id(user_id)

