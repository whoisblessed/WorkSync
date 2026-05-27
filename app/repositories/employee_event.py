from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_event import EmployeeEvent


class EmployeeEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, employee_id: int, event_id: int) -> EmployeeEvent:
        employee_event = EmployeeEvent(employee_id=employee_id, event_id=event_id)
        self.session.add(employee_event)
        await self.session.flush()
        return employee_event

    async def delete(self, employee_id: int, event_id: int) -> None:
        await self.session.execute(
            delete(EmployeeEvent).where(
                EmployeeEvent.employee_id == employee_id,
                EmployeeEvent.event_id == event_id,
            )
        )
        await self.session.flush()
