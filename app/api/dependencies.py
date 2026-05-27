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
from app.repositories import (
    UserRepository,
    TeamRepository,
    EmployeeRepository,
    ScheduleRepository,
    ScheduleExceptionRepository,
    EventRepository,
)
from app.services import (
    AuthService,
    UserService,
    TeamService,
    EmployeeService,
    ScheduleService,
    ScheduleExceptionService,
    EventService,
)


DBSession = Annotated[AsyncSession, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# Репозитории


def get_user_repository(session: DBSession) -> UserRepository:
    return UserRepository(session)


def get_team_repository(session: DBSession) -> TeamRepository:
    return TeamRepository(session)


def get_employee_repository(session: DBSession) -> EmployeeRepository:
    return EmployeeRepository(session)


def get_schedule_repository(session: DBSession) -> ScheduleRepository:
    return ScheduleRepository(session)


def get_schedule_exception_repository(
    session: DBSession,
) -> ScheduleExceptionRepository:
    return ScheduleExceptionRepository(session)


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
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> TeamService:
    return TeamService(team_repository, user_service)


def get_employee_service(
    employee_repository: Annotated[
        EmployeeRepository, Depends(get_employee_repository)
    ],
    user_service: Annotated[UserService, Depends(get_user_service)],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> EmployeeService:
    return EmployeeService(employee_repository, user_service, team_service)


def get_schedule_service(
    schedule_repository: Annotated[
        ScheduleRepository, Depends(get_schedule_repository)
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> ScheduleService:
    return ScheduleService(schedule_repository, employee_service)


def get_schedule_exception_service(
    schedule_exception_repository: Annotated[
        ScheduleExceptionRepository, Depends(get_schedule_exception_repository)
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> ScheduleExceptionService:
    return ScheduleExceptionService(
        schedule_exception_repository, employee_service, user_service
    )


def get_event_repository(session: DBSession) -> EventRepository:
    return EventRepository(session)


def get_event_service(
    event_repository: Annotated[EventRepository, Depends(get_event_repository)],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EventService:
    return EventService(event_repository, employee_service)


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


def get_user_with_roles(*roles: Role):
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