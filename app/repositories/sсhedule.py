from sqlalchemy import select

from app.models import Team, Employee, Schedule
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    model = Schedule

    async def get_by_user_id(self, id: int) -> Schedule | None:
        return await self.session.scalar(
            select(Schedule)
            .join(Employee)
            .where(Employee.user_id == id, Schedule.is_active)
        )

    async def get_by_employee_id(self, id: int) -> Schedule | None:
        return await self.session.scalar(
            select(Schedule).where(Schedule.employee_id == id)
        )

    async def get_all_by_manager_id(self, id: int) -> list[Schedule]:
        schedules = await self.session.scalars(
            select(Schedule)
            .join(Employee)
            .join(Team)
            .where(Team.manager_id == id, Schedule.is_active)
        )
        return schedules.all()
