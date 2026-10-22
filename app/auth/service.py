import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import EmailVerification
from app.auth.repository import AuthRepository
from app.auth.schemas import LoginRequest, RefreshRequest, RegisterCodeRequest, RegisterRequest, TokenPair
from app.core.config import settings
from app.core.email import notify_admin, send_email
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.users.models import User
from app.users.service import UserService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def request_registration_code(self, data: RegisterCodeRequest) -> dict[str, str]:
        if self.repo.get_user_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        code = f"{secrets.randbelow(1_000_000):06d}"
        verification = EmailVerification(
            email=data.email,
            code_hash=hash_password(code),
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.registration_code_expire_minutes),
        )
        self.repo.create_email_verification(verification)
        send_email(
            data.email,
            "BuildShop registration code",
            (
                "Your one-time registration code:\n\n"
                f"{code}\n\n"
                f"The code expires in {settings.registration_code_expire_minutes} minutes."
            ),
        )
        return {"detail": "Verification code sent"}

    def register(self, data: RegisterRequest) -> tuple[User, TokenPair]:
        # Check if user already exists
        if self.repo.get_user_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # Validate email verification code
        verification = self.repo.latest_email_verification(data.email)
        if verification:
            if verification.attempts >= 5:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many invalid code attempts")
            if not verify_password(data.verification_code, verification.code_hash):
                verification.attempts += 1
                self.db.add(verification)
                self.db.commit()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
            verification.consumed_at = datetime.now(UTC)
            self.db.add(verification)
        elif not settings.allow_registration_without_email:
            # No verification record and open registration not explicitly allowed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification required. Request a code first.",
            )
        user = UserService(self.db).create_user(data)
        notify_admin(
            "New BuildShop registration",
            f"New user registered:\n\nName: {user.full_name}\nEmail: {user.email}\nRole: {user.role.value}",
        )
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
