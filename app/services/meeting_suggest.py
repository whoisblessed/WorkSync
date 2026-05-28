from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Literal

import pytz

from app.models import Employee, User
from app.models.user import Role
from app.repositories.availability_map import AvailabilityRepository
from app.repositories.risk_analytics import RiskAnalyticsRepository
from app.schemas.meeting_suggest import (
    MeetingSlot,
    MeetingSuggestResponse,
    UnavailableReason,
)
from app.services.ai_assistant import _call_deepseek, _build_system_prompt, ChatMessage
from app.services.risk_analytics import RiskAnalyticsService, OVERLOAD_THRESHOLD

TOP_SLOTS = 3

EXCEPTION_LABELS: dict[str, str] = {
    "vacation": "Отпуск",
    "sick_leave": "Больничный",
    "personal": "Личные обстоятельства",
    "business_trip": "Командировка",
}


class MeetingSuggestService:
    def __init__(
        self,
        availability_repo: AvailabilityRepository,
        risk_repo: RiskAnalyticsRepository,
        api_key: str,
    ) -> None:
        self.availability_repo = availability_repo
        self.risk_repo = risk_repo
        self.api_key = api_key

    async def suggest(
        self,
        employee_ids: list[int],
        duration_minutes: int,
        days_ahead: int,
        current_user: User,
    ) -> MeetingSuggestResponse:
        user_tz_str = await self._get_user_tz(current_user)
        user_tz = pytz.timezone(user_tz_str)
        now_local = datetime.now(tz=user_tz)

        end_local = now_local + timedelta(days=days_ahead)
        months_to_load: set[tuple[int, int]] = set()
        cur = now_local
        while cur <= end_local:
            months_to_load.add((cur.year, cur.month))
            cur += timedelta(days=32)
            cur = cur.replace(day=1)

        manager_id = current_user.id if current_user.role == Role.manager else None

        emp_free: dict[int, set[tuple[date, int]]] = {
            eid: set() for eid in employee_ids
        }
        emp_objects: dict[int, Employee] = {}

        for year, month in months_to_load:
            employees = await self.availability_repo.get_active_employees_with_data(
                year=year,
                month=month,
                tz=user_tz_str,
                manager_id=manager_id,
            )
            for emp in employees:
                if emp.id not in employee_ids:
                    continue
                emp_objects[emp.id] = emp
                first_day = date(year, month, 1)
                last_day_excl = (
                    date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
                )
                d = first_day
                while d < last_day_excl:
                    for hour in range(8, 21):
                        if not self._is_unavailable_emp(emp, d, hour, user_tz):
                            emp_free[emp.id].add((d, hour))
                    d += timedelta(days=1)

        now_utc = datetime.now(tz=timezone.utc)
        period_start = now_utc - timedelta(days=30)
        risk_svc = RiskAnalyticsService()
        emp_load: dict[int, float] = {}
        for eid, emp in emp_objects.items():
            schedule = await self.risk_repo.get_schedule_for_employee(emp.id)
            events = await self.risk_repo.get_events_for_employee_in_period(
                emp.id, period_start, now_utc
            )
            exceptions = await self.risk_repo.get_exceptions_for_employee(emp.id)
            metrics = risk_svc.calculate_employee_metrics(
                emp, schedule, events, exceptions, analysis_days=30
            )
            emp_load[eid] = metrics.load_level

        slots_needed = max(1, (duration_minutes + 59) // 60)
        search_start = (now_local + timedelta(days=1)).date()
        search_end = (now_local + timedelta(days=days_ahead)).date()

        candidates: list[MeetingSlot] = []
        d = search_start
        while d <= search_end:
            for hour_start in range(8, 21 - slots_needed + 1):
                hours_block = list(range(hour_start, hour_start + slots_needed))
                unavailable_ids: list[int] = []

                for eid in employee_ids:
                    for h in hours_block:
                        if (d, h) not in emp_free.get(eid, set()):
                            unavailable_ids.append(eid)
                            break

                unavailable_ids = list(set(unavailable_ids))
                available_count = len(employee_ids) - len(unavailable_ids)

                unavailable_reasons, warnings = self._build_reasons_and_warnings(
                    unavailable_ids=unavailable_ids,
                    all_ids=employee_ids,
                    emp_objects=emp_objects,
                    emp_load=emp_load,
                    day=d,
                    hour_start=hour_start,
                    hours_block=hours_block,
                    user_tz=user_tz,
                    duration_minutes=duration_minutes,
                )

                candidates.append(
                    MeetingSlot(
                        date=d.isoformat(),
                        hour_start=hour_start,
                        hour_end=hour_start + slots_needed,
                        available_count=available_count,
                        total_count=len(employee_ids),
                        unavailable_employee_ids=unavailable_ids,
                        unavailable_reasons=unavailable_reasons,
                        warnings=warnings,
                    )
                )
            d += timedelta(days=1)

        candidates.sort(key=lambda s: (-s.available_count, s.date, s.hour_start))
        top = candidates[:TOP_SLOTS]

        ai_explanation = await self._explain(
            top, emp_objects, duration_minutes, user_tz_str
        )

        return MeetingSuggestResponse(slots=top, ai_explanation=ai_explanation)

    def _build_reasons_and_warnings(
        self,
        unavailable_ids: list[int],
        all_ids: list[int],
        emp_objects: dict[int, Employee],
        emp_load: dict[int, float],
        day: date,
        hour_start: int,
        hours_block: list[int],
        user_tz: pytz.BaseTzInfo,
        duration_minutes: int,
    ) -> tuple[list[UnavailableReason], list[str]]:
        reasons: list[UnavailableReason] = []
        warnings: list[str] = []

        for eid in unavailable_ids:
            emp = emp_objects.get(eid)
            if emp is None:
                continue

            name = f"{emp.last_name} {emp.first_name}"
            if emp.patronymic:
                name = f"{emp.last_name} {emp.first_name[0]}.{emp.patronymic[0]}."

            reason_type, reason_label = self._detect_reason(
                emp, day, hours_block, user_tz
            )
            reasons.append(
                UnavailableReason(
                    employee_id=eid,
                    full_name=name,
                    reason=reason_type,
                    reason_label=reason_label,
                )
            )
            warnings.append(f"{name} — {reason_label}")

        for eid in all_ids:
            if eid in unavailable_ids:
                continue
            load = emp_load.get(eid, 0.0)
            if load > OVERLOAD_THRESHOLD:
                emp = emp_objects.get(eid)
                if emp:
                    name = f"{emp.last_name} {emp.first_name}"
                    if emp.patronymic:
                        name = (
                            f"{emp.last_name} {emp.first_name[0]}.{emp.patronymic[0]}."
                        )
                    warnings.append(f"{name} — Перегрузка ({load:.0%})")

                    if duration_minutes > 30:
                        warnings.append(
                            f"Рекомендуется сократить встречу до 15–30 минут"
                        )

        return reasons, warnings

    def _detect_reason(
        self,
        emp: Employee,
        day: date,
        hours_block: list[int],
        user_tz: pytz.BaseTzInfo,
    ) -> tuple[str, str]:

        schedule = emp.schedule
        if schedule is None or not schedule.is_active:
            return "out_of_schedule", "Нет графика"

        if day.isoweekday() not in schedule.work_days:
            return "out_of_schedule", "Нерабочий день"

        for exc in getattr(emp, "_month_exceptions", []):
            if exc.start_date <= day <= exc.end_date:
                exc_type = (
                    exc.type.value if hasattr(exc.type, "value") else str(exc.type)
                )
                label = EXCEPTION_LABELS.get(exc_type, exc_type)
                return exc_type, label

        emp_tz = pytz.timezone(schedule.time_zone)
        for hour in hours_block:
            slot_start_utc = user_tz.localize(
                datetime(day.year, day.month, day.day, hour, 0, 0)
            ).astimezone(timezone.utc)
            slot_end_utc = slot_start_utc + timedelta(hours=1)

            for ev in getattr(emp, "_month_events", []):
                if ev.start_at < slot_end_utc and ev.end_at > slot_start_utc:
                    title = getattr(ev, "title", "")
                    label = f"Занят: {title}" if title else "Занят"
                    return "event", label

        return "out_of_schedule", "Вне рабочего времени"

    async def _get_user_tz(self, current_user: User) -> str:
        try:
            employee = current_user.employee
            if employee and employee.schedule and employee.schedule.time_zone:
                return employee.schedule.time_zone
        except Exception:
            pass
        return "UTC"

    def _is_unavailable_emp(
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

        work_start_utc = emp_tz.localize(
            datetime(
                day.year,
                day.month,
                day.day,
                schedule.start_at.hour,
                schedule.start_at.minute,
                0,
            )
        ).astimezone(timezone.utc)
        work_end_utc = emp_tz.localize(
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

        if slot_start_utc < work_start_utc or slot_end_utc > work_end_utc:
            return True

        for exc in getattr(emp, "_month_exceptions", []):
            if exc.start_date <= day <= exc.end_date:
                return True

        for ev in getattr(emp, "_month_events", []):
            if ev.start_at < slot_end_utc and ev.end_at > slot_start_utc:
                return True

        return False

    async def _explain(
        self,
        slots: list[MeetingSlot],
        emp_objects: dict[int, Employee],
        duration_minutes: int,
        tz_str: str,
    ) -> str:
        if not slots:
            return "Подходящих окон для встречи в указанном диапазоне не найдено."

        slots_text = ""
        for i, s in enumerate(slots, 1):
            warn_str = "; ".join(s.warnings) if s.warnings else "конфликтов нет"
            slots_text += (
                f"{i}. {s.date} {s.hour_start}:00–{s.hour_end}:00 "
                f"({s.available_count}/{s.total_count} участников; {warn_str})\n"
            )

        prompt = (
            f"Система подобрала топ-{len(slots)} окна для встречи "
            f"длительностью {duration_minutes} мин. в таймзоне {tz_str}:\n\n"
            f"{slots_text}\n"
            "Напиши краткое (3-4 предложения) объяснение для HR/менеджера: "
            "почему предложены именно эти слоты, на что обратить внимание. "
            "На русском языке."
        )
        return await _call_deepseek(
            self.api_key,
            _build_system_prompt(None),
            [ChatMessage(role="user", content=prompt)],
            max_tokens=400,
        )
