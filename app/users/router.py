from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.users.models import User
from app.users.schemas import AdminUserCreate, UserRead, UserUpdate
from app.users.service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_admin)])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[User]:
    return UserService(db).list_users(skip=skip, limit=limit)


@router.post("", response_model=UserRead, status_code=201, dependencies=[Depends(require_admin)])
def admin_create_user(payload: AdminUserCreate, db: Session = Depends(get_db)) -> User:
    return UserService(db).admin_create_user(payload)


@router.patch("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    return UserService(db).update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db)) -> Response:
    UserService(db).delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
