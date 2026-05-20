from sqlalchemy.exc import IntegrityError

from app.core.constants import ROLE_CREATION_PERMISSIONS
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.core.security import hash_password
from app.models import User
from app.models.user import Role
from app.shemas.user import UserCreate, UserFullCreate, UserUpdate
from app.repositories import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, id: int) -> User:
        db_user = await self.user_repository.get_by_id(id)
        if db_user is None:
            raise NotFoundException(f"Пользователь с ID {id} не найден или неактивен")

        return db_user

    async def register(self, user: UserCreate) -> User:
        try:
            return await self.user_repository.create(
                email=user.email,
                hashed_password=hash_password(user.password),
                role=Role.employee,
            )
        except IntegrityError:
            raise ConflictException(f"Пользователь с email {user.email} уже существует")

    async def register_user(self, user: UserFullCreate, current_user: User) -> User:
        if user.role not in ROLE_CREATION_PERMISSIONS.get(current_user.role, []):
            raise ForbiddenException(
                f"Пользователям с ролью {current_user.role.value} нельзя регистрировать пользователей с ролью {user.role.value}"
            )

        try:
            return await self.user_repository.create(
                email=user.email,
                hashed_password=hash_password(user.password),
                role=user.role,
            )
        except IntegrityError:
            raise ConflictException(f"Пользователь с email {user.email} уже существует")

    async def update(self, user: UserUpdate, current_user: User) -> User:
        db_user = await self.user_repository.get_by_id(current_user.id)
        if db_user is None:
            raise NotFoundException(
                f"Пользователь с ID {current_user.id} не найден или неактивен"
            )
        try:
            return await self.user_repository.update(
                db_user, **user.model_dump(exclude_none=True)
            )
        except IntegrityError:
            raise ConflictException(f"Пользователь с email {user.email} уже существует")

    async def deactivate_by_id(self, id: int) -> None:
        db_user = await self.user_repository.get_by_id(id)
        if db_user is None:
            raise NotFoundException(f"Пользователь с ID {id} не найден или неактивен")

        await self.user_repository.deactivate(db_user)

    async def activate_by_id(self, id: int) -> None:
        db_user = await self.user_repository.get_inactive_by_id(id)
        if db_user is None:
            raise NotFoundException(f"Пользователь с ID {id} не найден или активен")

        await self.user_repository.activate(db_user)
