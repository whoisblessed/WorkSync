from sqlalchemy import select

from app.models import Team, Employee, Event
from app.repositories import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    async def get_by_user_id(self, id: int) -> Employee | None:
        return await self.session.scalar(
            select(Employee).where(Employee.user_id == id, Employee.is_active)
        )

    async def get_all_by_manager_id(self, id: int) -> list[Employee]:
        employees = await self.session.scalars(
            select(Employee).join(Team).where(Team.manager_id == id, Employee.is_active)
        )
        return employees.all()

    async def get_all_by_event_id(self, id: int) -> list[Employee]:
        db_employees = self.session.scalars(select())
