from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Team
from app.repositories import BaseRepository


class TeamRepository(BaseRepository[Team]):
    model = Team

    async def get_by_id(self, id: int) -> Team:
        return await self.session.scalar(
            select(Team)
            .where(Team.id == id, Team.is_active)
            .options(selectinload(Team.employees))
        )

    async def get_by_name(self, name: str) -> Team:
        return await self.session.scalar(
            select(Team)
            .where(Team.name == name, Team.is_active)
            .options(selectinload(Team.employees))
        )
