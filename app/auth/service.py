from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.repository import AuthRepository
from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.core.config import settings
from app.core.security import create_token, decode_token, verify_password
from app.users.models import User
from app.users.service import UserService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def register(self, data: RegisterRequest) -> tuple[User, TokenPair]:
        user = UserService(self.db).create_user(data)
        return user, self._build_tokens(user)

    def login(self, data: LoginRequest) -> TokenPair:
        user = self.repo.get_user_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        return self._build_tokens(user)

    def refresh(self, data: RefreshRequest) -> TokenPair:
        try:
            payload = decode_token(data.refresh_token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type")
        user_id = payload.get("sub")
        user = self.repo.get_user_by_id(int(user_id)) if user_id else None
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return self._build_tokens(user)

    def _build_tokens(self, user: User) -> TokenPair:
        claims = {"role": user.role.value}
        access = create_token(
            str(user.id),
            "access",
            timedelta(minutes=settings.access_token_expire_minutes),
            claims,
        )
        refresh = create_token(
            str(user.id),
            "refresh",
            timedelta(days=settings.refresh_token_expire_days),
            claims,
        )
        return TokenPair(access_token=access, refresh_token=refresh)

