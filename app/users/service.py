from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import AdminUserCreate, UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        return self.repo.create(user)

    def admin_create_user(self, data: AdminUserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        return self.repo.create(user)

    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.repo.list(skip=skip, limit=limit)

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        return self.repo.update(user)

    def delete_user(self, user_id: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        self.repo.delete(user)
