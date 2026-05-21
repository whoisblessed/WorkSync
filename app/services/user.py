from sqlalchemy.exc import IntegrityError

from app.core.exceptions import NotFoundException, ConflictException
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

    async def register_user(self, user: UserFullCreate) -> User:
        try:
            return await self.user_repository.create(
                email=user.email,
                hashed_password=hash_password(user.password),
                role=user.role,
            )
        except IntegrityError:
            raise ConflictException(f"Пользователь с email {user.email} уже существует")

    async def update(self, id: int, user: UserUpdate) -> User:
        db_user = await self.get_by_id(id)
        try:
            return await self.user_repository.update(
                db_user,
                email=user.email,
                hashed_password=hash_password(user.password),
                role=user.role,
            )
        except IntegrityError:
            raise ConflictException(f"Пользователь с email {user.email} уже существует")

    async def deactivate_by_id(self, id: int) -> None:
        db_user = await self.get_by_id(id)
        await self.user_repository.deactivate(db_user)

    async def activate_by_id(self, id: int) -> None:
        db_user = await self.user_repository.get_inactive_by_id(id)
        if db_user is None:
            raise NotFoundException(f"Пользователь с ID {id} не найден или активен")

        await self.user_repository.activate(db_user)
