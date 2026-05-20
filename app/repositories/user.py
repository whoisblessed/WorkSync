from sqlalchemy import select

from app.models import User
from app.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(
            select(User).where(User.email == email, User.is_active)
        )
