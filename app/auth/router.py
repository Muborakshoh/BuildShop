from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterCodeRequest,
    RegisterCodeResponse,
    RegisterRequest,
    RegisterResponse,
    TokenPair,
)
from app.auth.service import AuthService
from app.core.dependencies import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/request-code", response_model=RegisterCodeResponse)
def request_register_code(payload: RegisterCodeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    return AuthService(db).request_registration_code(payload)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    user, tokens = AuthService(db).register(payload)
    return RegisterResponse(user=user, tokens=tokens)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    return AuthService(db).login(payload)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    return AuthService(db).refresh(payload)
