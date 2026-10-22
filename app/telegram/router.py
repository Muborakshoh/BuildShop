"""Telegram auth endpoints + notification settings."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.service import AuthService
from app.core.dependencies import get_current_user, get_db
from app.telegram.bot import verify_telegram_login
from app.users.models import User

router = APIRouter(prefix="/telegram", tags=["telegram"])


class TelegramLoginData(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class TelegramLinkData(BaseModel):
    telegram_id: int
    first_name: str
    username: str | None = None
    hash: str
    auth_date: int


@router.post("/auth")
def telegram_auth(data: TelegramLoginData, db: Session = Depends(get_db)):
    """Authenticate or register via Telegram Login Widget."""
    raw = data.model_dump()
    if not verify_telegram_login(dict(raw)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth data")

    # Find user by telegram_id
    user = db.query(User).filter(User.telegram_id == data.id).first()
    if user:
        # Login existing user
        auth = AuthService(db)
        tokens = auth.create_token_pair(user)
        return {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token, "user_id": user.id}

    # Register new user
    full_name = data.first_name
    if data.last_name:
        full_name += f" {data.last_name}"

    user = User(
        email=f"tg_{data.id}@telegram.local",
        full_name=full_name,
        hashed_password="telegram_auth_no_password",
        telegram_id=data.id,
        telegram_username=data.username,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    auth = AuthService(db)
    tokens = auth.create_token_pair(user)
    return {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token, "user_id": user.id}


@router.post("/link")
def link_telegram(data: TelegramLinkData, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Link Telegram account to existing user for notifications."""
    raw = data.model_dump()
    if not verify_telegram_login(dict(raw)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram data")

    # Check if this telegram_id is already linked to another user
    existing = db.query(User).filter(User.telegram_id == data.telegram_id).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telegram account already linked")

    current_user.telegram_id = data.telegram_id
    current_user.telegram_username = data.username
    db.commit()
    return {"status": "linked", "telegram_id": data.telegram_id}


@router.delete("/link")
def unlink_telegram(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Unlink Telegram from user account."""
    current_user.telegram_id = None
    current_user.telegram_username = None
    db.commit()
    return {"status": "unlinked"}
