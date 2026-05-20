from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Schedule
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    model = Schedule

    async def get_by_employee_id(self, employee_id: int) -> Schedule | None:
        return await self.session.scalar(
            select(Schedule)
            .where(Schedule.employee_id == employee_id, Schedule.is_active)
            .options(selectinload(Schedule.employee))
        )
