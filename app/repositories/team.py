from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Team, Employee
from app.repositories import BaseRepository


class TeamRepository(BaseRepository[Team]):
    model = Team

    # ПОлучаем тиму по названию
    async def get_by_name(self, name: str) -> Team:
        return await self.session.scalar(
            select(Team).where(Team.name == name, Team.is_active)
        )

    # Получаем команды, которыми управляет конкретный менеджер, насколько я понял. точно ли это тут должно быть? :/
    async def get_all_by_manager_id(self, manager_id: int) -> list[Team]:
        return await self.session.scalars(
            select(Team)
            .where(Team.manager_id == manager_id, Team.is_active)
            .options(selectinload(Team.manager))
        )

    # Получаем тиму со всеми ее членами

    async def get_members_by_team_id(self, team_id: int) -> Team | None:
        find_team = await self.session.execute(
            select(Team).where(Team.id == team_id, Team.is_active == True)
        )
        team = find_team.scalar_or_none()

        if not team:
            return None

        members = await self.session.execute(
            select(Employee).where(Employee.team_id == team_id)
        )

        team.members = list(members.scalars().all())

        return team

