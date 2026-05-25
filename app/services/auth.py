import jwt

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import UnauthorizedException
from app.models import User
from app.schemas.token import AccessToken, Tokens
from app.repositories import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedException()

        return user

    def issue_access_token(self, user: User) -> AccessToken:
        return AccessToken(
            access_token=create_access_token(
                {"sub": user.email, "role": user.role.value}
            )
        )

    def issue_tokens(self, user: User) -> Tokens:
        return Tokens(
            access_token=create_access_token(
                {"sub": user.email, "role": user.role.value}
            ),
            refresh_token=create_refresh_token({"sub": user.email}),
        )

    async def login(self, email: str, password: str) -> Tokens:
        user = await self.authenticate(email, password)
        return self.issue_tokens(user)

    async def refresh(self, refresh_token: str) -> Tokens:
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Токен был просрочен")
        except jwt.PyJWTError:
            raise UnauthorizedException()

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Неправильный тип токена")

        user = await self.user_repository.get_by_email(payload.get("sub"))
        if user is None:
            raise UnauthorizedException("Пользователь не найден или неактивен")

        return self.issue_tokens(user)
