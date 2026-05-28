from datetime import date, datetime, timedelta, timezone

import pytz

from app.models import Employee, User
from app.models.user import Role
from app.repositories.availability_map import AvailabilityRepository
from app.schemas.availability_map import AvailabilityResponse, AvailabilitySlot


class AvailabilityMapService:
    def __init__(self, availability_repository: AvailabilityRepository) -> None:
        self.availability_repository = availability_repository

    async def get_availability_map(
        self,
        month: int,
        current_user: User,
    ) -> AvailabilityResponse:
        # Resolve the current user's timezone from their own schedule.
        # The schedule is loaded via the repository for the manager/HR themselves;
        # fall back to UTC if not set.
        user_tz_str = await self._get_user_tz(current_user)
        user_tz = pytz.timezone(user_tz_str)

        year = datetime.now(tz=user_tz).year

        manager_id = current_user.id if current_user.role == Role.manager else None

        employees = await self.availability_repository.get_active_employees_with_data(
            year=year,
            month=month,
            tz=user_tz_str,
            manager_id=manager_id,
        )

        total = len(employees)
        slots = self._compute_slots(employees, year, month, user_tz)

        return AvailabilityResponse(
            month=month,
            year=year,
            total=total,
            slots=slots,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_user_tz(self, current_user: User) -> str:
        """
        Pull the timezone from the current HR/manager's own schedule.
        The employee relationship is loaded lazily by SQLAlchemy; we read
        the schedule from the already-loaded relationship chain when possible,
        otherwise default to UTC.
        """
        try:
            employee = current_user.employee  # may trigger lazy load
            if employee and employee.schedule and employee.schedule.time_zone:
                return employee.schedule.time_zone
        except Exception:
            pass
        return "UTC"

    def _compute_slots(
        self,
        employees: list[Employee],
        year: int,
        month: int,
        user_tz: pytz.BaseTzInfo,
    ) -> list[AvailabilitySlot]:
        """
        For every (date, hour) slot in the month produce an AvailabilitySlot.
        Hours are in the HR/manager timezone (8:00–20:00 visible range in UI,
        but we generate all working hours found across all employees' schedules).

        Slot hours go from 0..23; the front-end filters to the displayed range.
        We generate 8–20 inclusive to match the mockup.
        """
        # Determine month date range
        first_day = date(year, month, 1)
        if month == 12:
            last_day_exclusive = date(year + 1, 1, 1)
        else:
            last_day_exclusive = date(year, month + 1, 1)

        slots: list[AvailabilitySlot] = []
        current_date = first_day

        while current_date < last_day_exclusive:
            for hour in range(8, 21):  # 8:00 .. 20:00 inclusive
                unavailable_ids: list[int] = []

                for emp in employees:
                    if self._is_unavailable(emp, current_date, hour, user_tz):
                        unavailable_ids.append(emp.id)

                available = len(employees) - len(unavailable_ids)
                slots.append(
                    AvailabilitySlot(
                        date=current_date.isoformat(),
                        hour=hour,
                        available=available,
                        total=len(employees),
                        unavailable_employee_ids=unavailable_ids,
                    )
                )

            current_date += timedelta(days=1)

        return slots

    def _is_unavailable(
        self,
        emp: Employee,
        day: date,
        hour: int,
        viewer_tz: pytz.BaseTzInfo,
    ) -> bool:
        """
        Returns True if the employee is unavailable for the given (day, hour) slot.

        Reasons for unavailability:
        1. No active schedule.
        2. day-of-week not in their work_days (ISO: Mon=1 … Sun=7).
        3. The slot hour is outside their work hours (converted to the viewer's tz).
        4. A ScheduleException covers this date (vacation, sick leave, etc.).
        5. An Event overlaps [hour, hour+1) on this date.
        """
        schedule = emp.schedule
        if schedule is None or not schedule.is_active:
            return True

        # --- day-of-week check (schedule.work_days uses ISO weekday 1-7) ---
        if day.isoweekday() not in schedule.work_days:
            return True

        # --- work-hour check ---
        # Convert the employee's schedule times to the viewer's timezone for the
        # specific date, so the map always shows hours in the viewer's local time.
        emp_tz = pytz.timezone(schedule.time_zone)

        # Slot start/end in viewer tz
        slot_start_viewer = viewer_tz.localize(
            datetime(day.year, day.month, day.day, hour, 0, 0)
        )
        slot_end_viewer = slot_start_viewer + timedelta(hours=1)

        # Employee's work window for this day in UTC
        work_start_emp = emp_tz.localize(
            datetime(
                day.year,
                day.month,
                day.day,
                schedule.start_at.hour,
                schedule.start_at.minute,
                0,
            )
        ).astimezone(timezone.utc)
        work_end_emp = emp_tz.localize(
            datetime(
                day.year,
                day.month,
                day.day,
                schedule.end_at.hour,
                schedule.end_at.minute,
                0,
            )
        ).astimezone(timezone.utc)

        slot_start_utc = slot_start_viewer.astimezone(timezone.utc)
        slot_end_utc = slot_end_viewer.astimezone(timezone.utc)

        # Slot must be fully inside the work window
        if slot_start_utc < work_start_emp or slot_end_utc > work_end_emp:
            return True

        # --- ScheduleException check ---
        for exc in emp._month_exceptions:  # type: ignore[attr-defined]
            if exc.start_date <= day <= exc.end_date:
                return True

        # --- Event overlap check ---
        for ev in emp._month_events:  # type: ignore[attr-defined]
            # event times are tz-aware; compare with slot in UTC
            if ev.start_at < slot_end_utc and ev.end_at > slot_start_utc:
                return True

        return False
