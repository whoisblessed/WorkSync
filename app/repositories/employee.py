from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Employee, Team
from app.repositories import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    async def get_by_user_id(self, user_id: int):
        return await self.session.scalar(
            select(Employee)
            .where(Employee.user_id == user_id, Employee.is_active)
            .options(selectinload(Employee.user))
        )
