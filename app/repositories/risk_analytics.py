"""
Репозиторий для аналитики рисков.
Содержит запросы, необходимые для расчёта метрик по экрану «Конфликты и риски».
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Employee, Event, Schedule, ScheduleException, Team
from app.models.employee_event import EmployeeEvent


class RiskAnalyticsRepository:
    """
    Не наследует BaseRepository — работает с несколькими моделями
    и предоставляет специфичные запросы для аналитики.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_employees_with_relations(
        self,
        manager_user_id: int | None = None,
        team_id: int | None = None,
    ) -> list[Employee]:
        """
        Возвращает список активных сотрудников с предзагруженными
        schedule и schedule_exceptions.

        - manager_user_id: если передан, возвращает только сотрудников из команд этого менеджера.
        - team_id: дополнительный фильтр по команде.
        """
        stmt = (
            select(Employee)
            .options(
                selectinload(Employee.schedule),
                selectinload(Employee.schedule_exceptions),
            )
            .where(Employee.is_active)
        )

        if team_id is not None:
            stmt = stmt.where(Employee.team_id == team_id)
        elif manager_user_id is not None:
            stmt = stmt.join(Team).where(
                Team.manager_id == manager_user_id, Employee.is_active
            )

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_events_for_employee_in_period(
        self,
        employee_id: int,
        period_start: datetime,
        period_end: datetime,
    ) -> list[Event]:
        """
        Возвращает все активные события сотрудника в заданном временном диапазоне.
        """
        stmt = (
            select(Event)
            .join(EmployeeEvent, Event.id == EmployeeEvent.event_id)
            .where(
                EmployeeEvent.employee_id == employee_id,
                Event.is_active,
                Event.start_at >= period_start,
                Event.start_at <= period_end,
            )
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_schedule_for_employee(
        self, employee_id: int
    ) -> Schedule | None:
        """Возвращает активное расписание сотрудника."""
        return await self.session.scalar(
            select(Schedule).where(
                Schedule.employee_id == employee_id,
                Schedule.is_active,
            )
        )

    async def get_exceptions_for_employee(
        self, employee_id: int
    ) -> list[ScheduleException]:
        """Возвращает все активные исключения (отпуска, больничные …) сотрудника."""
        result = await self.session.scalars(
            select(ScheduleException).where(
                ScheduleException.employee_id == employee_id,
                ScheduleException.is_active,
            )
        )
        return list(result.all())