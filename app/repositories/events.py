from sqlalchemy import select

from app.models import Event, Employee, EmployeeEvent
from app.repositories import BaseRepository


class EventRepository(BaseRepository[Event]):

    model = Event

    async def get_by_employee_id(
            self, employee_id: int, include_inactive: bool = False
    ) -> list[Event]:
        # Получить все события конкретного сотрудника
        query = select(Event).join(
            EmployeeEvent, Event.id == EmployeeEvent.event_id
        ).where(EmployeeEvent.employee_id == employee_id)

        if not include_inactive:
            query = query.where(Event.is_active)

        result = await self.session.scalars(query)
        return list(result.all())

    async def update_employees(
            self, event_id: int, employee_ids: list[int]
    ) -> None:
        # Обновление списка сотрудников, участвующих в событии
        event = await self.session.get(Event, event_id)
        if not event:
            return

        # Очистка старых связей
        event.employees = []

        # Получаем новых сотрудников
        employees = await self.session.scalars(
            select(Employee).where(Employee.id.in_(employee_ids))
        )

        # Устанавливаем новые связи
        event.employees = list(employees.all())
