from sqlalchemy.exc import IntegrityError, MultipleResultsFound

from app.core.exceptions import NotFoundException, ConflictException
from app.models import User
from app.shemas.user import UserCreate
from app.repositories import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, user: UserCreate) -> User:
        try:
            db_user = await self.user_repository.create(**user.model_dump())
        except IntegrityError:
            raise ConflictException(f"Пользователь с email {user.email} уже существует")

        return db_user

    async def activate_user_by_id(self, id: int) -> None:
        try:
            user = self.user_repository.get_active_by_id(id)
        except MultipleResultsFound:
            raise ConflictException("")
