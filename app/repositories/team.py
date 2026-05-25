from sqlalchemy import select

from app.models import Employee, Team
from app.repositories import BaseRepository


class TeamRepository(BaseRepository[Team]):
    model = Team

    async def get_by_user_id(self, id: int) -> Team:
        return await self.session.scalar(
            select(Team).join(Employee).where(Employee.user_id == id, Team.is_active)
        )

    async def get_all_by_manager_id(self, id: int) -> list[Team]:
        teams = await self.session.scalars(
            select(Team).where(Team.manager_id == id, Team.is_active)
        )
        return teams.all()
