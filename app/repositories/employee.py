from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Team, Employee
from app.repositories import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    async def get_by_user_id(self, id: int) -> Employee:
        return await self.session.scalar(
            select(Employee)
            .where(Employee.user_id == id, Employee.is_active)
            .options(selectinload(Employee.user))
        )

    async def get_all_by_team_id(self, id: int) -> list[Employee]:
        return await self.session.scalars(
            select(Employee)
            .where(Employee.team_id == id, Employee.is_active)
            .options(selectinload(Employee.team))
        )

    async def get_all_by_manager_id(self, id: int) -> list[Employee]:
        return await self.session.scalars(
            select(Employee).join(Team).where(Team.manager_id == id, Employee.is_active)
        )
