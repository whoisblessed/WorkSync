from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Team
from app.repositories import BaseRepository


class TeamRepository(BaseRepository[Team]):
    model = Team

    async def get_by_name(self, name: str) -> Team:
        return await self.session.scalar(
            select(Team).where(Team.name == name, Team.is_active)
        )

    async def get_all_by_manager_id(self, manager_id: int) -> list[Team]:
        return await self.session.scalars(
            select(Team)
            .where(Team.manager_id == manager_id, Team.is_active)
            .options(selectinload(Team.manager))
        )
