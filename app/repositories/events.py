from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models import Event, Employee, Team, EmployeeEvent
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event


    def _with_employees(self):
        """Опция загрузки участников вместе с событием."""
        return selectinload(Event.employees)


    async def get_all(self) -> list[Event]:
        result = await self.session.scalars(
            select(Event)
            .where(Event.is_active)
            .options(self._with_employees())
        )
        return result.all()

    async def get_by_id(self, obj_id: int) -> Event | None:
        return await self.session.scalar(
            select(Event)
            .where(Event.id == obj_id, Event.is_active)
            .options(self._with_employees())
        )

    async def get_all_by_manager_id(self, manager_id: int) -> list[Event]:
        """События, у которых хотя бы один участник из команды менеджера."""
        result = await self.session.scalars(
            select(Event)
            .join(Event.employees)
            .join(Employee.team)
            .where(Team.manager_id == manager_id, Event.is_active)
            .distinct()
            .options(self._with_employees())
        )
        return result.all()

    async def get_all_by_employee_id(self, employee_id: int) -> list[Event]:
        """События конкретного сотрудника."""
        result = await self.session.scalars(
            select(Event)
            .join(Event.employees)
            .where(Employee.id == employee_id, Event.is_active)
            .options(self._with_employees())
        )
        return result.all()


    async def create_with_employees(
        self, employees: list[Employee], **kwargs
    ) -> Event:
        event = Event(**kwargs)
        event.employees = employees

        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event, attribute_names=["employees"])

        return event

    async def set_employees(self, event: Event, employees: list[Employee]) -> Event:
        """Заменяет список участников события."""
        await self.session.execute(
            delete(EmployeeEvent).where(EmployeeEvent.event_id == event.id)
        )
        event.employees = employees
        await self.session.flush()
        await self.session.refresh(event, attribute_names=["employees"])
        return event