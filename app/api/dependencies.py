from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User
from app.models.user import Role
from app.repositories import UserRepository, TeamRepository
from app.services import AuthService, UserService, TeamService


DBSession = Annotated[AsyncSession, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# Репозитории


def get_user_repository(session: DBSession) -> UserRepository:
    return UserRepository(session)


def get_team_repository(session: DBSession) -> TeamRepository:
    return TeamRepository(session)


# Сервисы


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repository)


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repository)


def get_team_service(
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> TeamService:
    return TeamService(team_repository)


# Аутентификация


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    if token is None:
        raise UnauthorizedException("Токен не предоставлен")

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Токен просрочен")
    except jwt.PyJWTError:
        raise UnauthorizedException()

    if payload.get("type") != "access":
        raise UnauthorizedException("Неверный тип токена")

    user = await user_repository.get_by_email(payload.get("sub"))
    if user is None:
        raise UnauthorizedException("Пользователь не найден или неактивен")

    return user


def user_require_roles(*roles: Role):
    roles_str = ", ".join([role.value for role in roles])

    async def get_current_user_with_role(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in roles:
            raise ForbiddenException(
                f"Действие доступно только пользователям с правами: {roles_str}"
            )

        return user

    return get_current_user_with_role
