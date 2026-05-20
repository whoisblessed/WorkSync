from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Employee
from app.repositories import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    async def get_by_user_id(self, user_id: int) -> Employee:
        return await self.session.scalar(
            select(Employee)
            .where(Employee.user_id == user_id, Employee.is_active)
            .options(selectinload(Employee.user))
        )

    async def get_all_by_team_id(self, team_id: int) -> list[Employee]:
        return await self.session.scalars(
            select(Employee)
            .where(Employee.team_id == team_id, Employee.is_active)
            .options(selectinload(Employee.team))
        )
