from fastapi import APIRouter, Depends, Request
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
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/request-code", response_model=RegisterCodeResponse)
def request_register_code(payload: RegisterCodeRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    rate_limit(request, key_prefix="auth:register-code", max_calls=5, window_seconds=900)
    return AuthService(db).request_registration_code(payload)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> RegisterResponse:
    rate_limit(request, key_prefix="auth:register", max_calls=10, window_seconds=3600)
    user, tokens = AuthService(db).register(payload)
    return RegisterResponse(user=user, tokens=tokens)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    rate_limit(request, key_prefix="auth:login", max_calls=20, window_seconds=900)
    return AuthService(db).login(payload)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    rate_limit(request, key_prefix="auth:refresh", max_calls=30, window_seconds=3600)
    return AuthService(db).refresh(payload)
