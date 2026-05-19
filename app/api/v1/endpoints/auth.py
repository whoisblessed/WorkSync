from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_auth_service
from app.shemas.token import Tokens, AccessToken, RefreshTokenRequest
from app.services import AuthService


router = APIRouter(prefix="/auth")


@router.post("/login", response_model=Tokens)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Tokens:
    """Выполняет логин пользователя, возвращает access и refresh JWT"""
    return await auth_service.login(form_data.username, form_data.password)


@router.post("/refresh", response_model=Tokens)
async def refresh_token(
    refresh_token: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessToken:
    """Выдает новый access JWT по refresh JWT"""
    return await auth_service.refresh(refresh_token.refresh_token)
