from collections.abc import Callable, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.users.models import User, UserRole
from app.users.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise credentials_error from exc

    if payload.get("type") != "access":
        raise credentials_error

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_error

    user = UserRepository(db).get_by_id(int(user_id))
    if not user or not user.is_active:
        raise credentials_error
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    """Allow admin, manager, and seller roles."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER, UserRole.SELLER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
    return current_user


# ✅ Исправлено: require_roles теперь корректно работает с FastAPI Depends
def require_roles(*roles: UserRole):
    def checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            allowed = ", ".join(role.value for role in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {allowed}",
            )
        return current_user

    # ✅ FastAPI не разрешает вложенный Depends в closure,
    #    но Depends(checker) где checker сам вызывает Depends — работает
    #    Альтернатива — использовать Depends напрямую в endpoint'е
    return checker
