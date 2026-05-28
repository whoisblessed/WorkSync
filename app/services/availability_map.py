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

    async def _get_user_tz(self, current_user: User) -> str:
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
        # Determine month date range
        first_day = date(year, month, 1)
        if month == 12:
            last_day_exclusive = date(year + 1, 1, 1)
        else:
            last_day_exclusive = date(year, month + 1, 1)

        slots: list[AvailabilitySlot] = []
        current_date = first_day

        while current_date < last_day_exclusive:
            for hour in range(8, 21):
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
        schedule = emp.schedule
        if schedule is None or not schedule.is_active:
            return True

        if day.isoweekday() not in schedule.work_days:
            return True

        emp_tz = pytz.timezone(schedule.time_zone)

        slot_start_viewer = viewer_tz.localize(
            datetime(day.year, day.month, day.day, hour, 0, 0)
        )
        slot_end_viewer = slot_start_viewer + timedelta(hours=1)

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

        if slot_start_utc < work_start_emp or slot_end_utc > work_end_emp:
            return True

        for exc in emp._month_exceptions:
            if exc.start_date <= day <= exc.end_date:
                return True

        for ev in emp._month_events:
            if ev.start_at < slot_end_utc and ev.end_at > slot_start_utc:
                return True

        return False
