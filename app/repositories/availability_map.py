from datetime import date, datetime, timezone

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Employee


class AvailabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_employees_with_data(
        self,
        year: int,
        month: int,
        tz: str,
        manager_id: int | None = None,
    ) -> list[Employee]:
        """
        Returns all active employees (optionally filtered by manager)
        with their schedule, schedule_exceptions and events eagerly loaded.
        Only exceptions and events that overlap the requested month are included.
        """
        from app.models import Team

        # First/last day of the month in the HR/manager timezone
        user_tz = pytz.timezone(tz)
        first_day = date(year, month, 1)
        # last day of month
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)

        # month start/end as tz-aware datetimes for event overlap check
        month_start_dt = user_tz.localize(datetime(year, month, 1, 0, 0, 0)).astimezone(
            timezone.utc
        )
        month_end_dt = user_tz.localize(
            datetime(last_day.year, last_day.month, last_day.day, 0, 0, 0)
        ).astimezone(timezone.utc)

        # Build employee query
        stmt = (
            select(Employee)
            .where(Employee.is_active)
            .options(
                selectinload(Employee.schedule),
                selectinload(Employee.schedule_exceptions),
                selectinload(Employee.events),
            )
        )
        if manager_id is not None:
            stmt = stmt.join(Team).where(Team.manager_id == manager_id)

        employees = (await self.session.scalars(stmt)).all()

        # Filter exceptions and events to the month in Python
        # (avoids complex subquery joins while keeping code readable)
        result = []
        for emp in employees:
            # Keep only exceptions that overlap [first_day, last_day)
            emp._month_exceptions = [
                exc
                for exc in emp.schedule_exceptions
                if exc.is_active
                and exc.start_date < last_day
                and exc.end_date >= first_day
            ]
            # Keep only events that overlap the month window (UTC comparison)
            emp._month_events = [
                ev
                for ev in emp.events
                if ev.is_active
                and ev.start_at < month_end_dt
                and ev.end_at > month_start_dt
            ]
            result.append(emp)

        return result
