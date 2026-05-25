from sqlalchemy import select

from app.models import User, Team, Employee, ScheduleException
from app.repositories.base import BaseRepository


class ScheduleExceptionRepository(BaseRepository[ScheduleException]):
    model = ScheduleException

    async def get_all_by_user_id(self, id: int) -> list[ScheduleException]:
        schedule_exceptions = await self.session.scalars(
            select(ScheduleException).join(Employee).where(Employee.user_id == id)
        )

        return schedule_exceptions.all()

    async def get_all_by_manager_id(self, id: int) -> list[ScheduleException]:
        schedule_exceptions = await self.session.scalars(
            select(ScheduleException)
            .join(Employee)
            .join(Team)
            .where(Team.manager_id == id)
        )

        return schedule_exceptions.all()
