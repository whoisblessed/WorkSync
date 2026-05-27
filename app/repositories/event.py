from sqlalchemy import select

from app.models import Team, Employee, Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    async def get_all_by_user_id(self, id: int) -> list[Event]:
        db_events = await self.session.scalars(
            select(Event).join(Employee).where(Employee.user_id == id, Event.is_active)
        )
        return db_events.all()

    async def get_all_by_manager_id(self, id: int) -> list[Event]:
        db_events = await self.session.scalars(
            select(Event)
            .join(Employee)
            .join(Team)
            .where(Team.manager_id == id, Event.is_active)
        )
        return db_events.all()
