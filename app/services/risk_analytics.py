from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone, timedelta
from typing import Sequence
import zoneinfo

from app.models import Employee, Schedule, ScheduleException, Event

MAX_DAYS_WITHOUT_UPDATE: int = 90


OVERLOAD_THRESHOLD: float = 0.8

LATE_HOUR_THRESHOLD: int = 20

DEFAULT_ANALYSIS_DAYS: int = 30

W1_ACTUALITY: float = 0.25
W2_CONFLICTS: float = 0.25
W3_LOAD: float = 0.20
W4_TIMEZONE: float = 0.15
W5_HR_MISMATCH: float = 0.15



@dataclass
class EmployeeRiskMetrics:
    employee_id: int
    first_name: str
    last_name: str
    patronymic: str | None

    actuality_score: float
    days_since_update: int

    out_of_schedule_ratio: float
    meetings_out: int
    meetings_total: int

    load_level: float
    hours_busy: float
    hours_work: float

    timezone_conflict: float
    timezone_note: str

    hr_calendar_mismatch: float

    integral_risk: float

    active_exceptions: list[str] = field(default_factory=list)

    recommendations: list[str] = field(default_factory=list)

    has_exceptions: bool = False

    time_zone: str = "Europe/Moscow"

    work_format: str = "office"


@dataclass
class TeamRiskSummary:
    employees: list[EmployeeRiskMetrics]
    total_employees: int
    outdated_count: int
    overloaded_count: int
    tz_conflict_count: int
    high_risk_count: int



def _make_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _is_event_outside_schedule(
    event_start: datetime,
    event_end: datetime,
    schedule: Schedule,
) -> bool:

    try:
        tz = zoneinfo.ZoneInfo(schedule.time_zone)
    except (KeyError, zoneinfo.ZoneInfoNotFoundError):
        tz = timezone.utc

    local_start = _make_aware(event_start).astimezone(tz)

    iso_weekday = local_start.isoweekday()
    if iso_weekday not in schedule.work_days:
        return True

    event_time = local_start.time()
    if event_time < schedule.start_at or event_time >= schedule.end_at:
        return True

    return False


def _count_working_hours(
    start_dt: datetime,
    end_dt: datetime,
    schedule: Schedule,
) -> float:
    try:
        tz = zoneinfo.ZoneInfo(schedule.time_zone)
    except (KeyError, zoneinfo.ZoneInfoNotFoundError):
        tz = timezone.utc

    work_start = start_dt.astimezone(tz).date()
    work_end = end_dt.astimezone(tz).date()

    hours_per_day = (
        datetime.combine(date.today(), schedule.end_at)
        - datetime.combine(date.today(), schedule.start_at)
    ).seconds / 3600.0

    total = 0.0
    current = work_start
    while current <= work_end:
        if current.isoweekday() in schedule.work_days:
            total += hours_per_day
        current += timedelta(days=1)

    return total


def _count_busy_hours(events: Sequence[Event]) -> float:
    total = 0.0
    for ev in events:
        start = _make_aware(ev.start_at)
        end = _make_aware(ev.end_at)
        total += max(0.0, (end - start).total_seconds() / 3600.0)
    return total


def _detect_timezone_conflict(
    events: Sequence[Event],
    schedule: Schedule,
) -> tuple[float, str]:

    if not events:
        return 0.0, ""

    try:
        tz = zoneinfo.ZoneInfo(schedule.time_zone)
    except (KeyError, zoneinfo.ZoneInfoNotFoundError):
        tz = timezone.utc

    late_count = sum(
        1 for ev in events
        if _make_aware(ev.start_at).astimezone(tz).hour >= LATE_HOUR_THRESHOLD
    )

    ratio = late_count / len(events)
    if ratio > 0.2:
        return 1.0, (
            f"Указан часовой пояс {schedule.time_zone}, "
            f"а встречи после {LATE_HOUR_THRESHOLD}:00 — {late_count} из {len(events)}"
        )
    return 0.0, ""


def _detect_hr_calendar_mismatch(
    schedule: Schedule,
    events: Sequence[Event],
    exceptions: Sequence[ScheduleException],
) -> float:
    if not exceptions:
        return 0.0

    exception_dates: set[date] = set()
    for exc in exceptions:
        cur = exc.start_date
        while cur <= exc.end_date:
            exception_dates.add(cur)
            cur += timedelta(days=1)

    if not exception_dates:
        return 0.0

    event_dates_in_exception = set()
    for ev in events:
        ev_date = _make_aware(ev.start_at).date()
        if ev_date in exception_dates:
            event_dates_in_exception.add(ev_date)

    mismatch = len(event_dates_in_exception) / len(exception_dates)
    return min(mismatch, 1.0)


def _build_recommendations(metrics: EmployeeRiskMetrics) -> list[str]:
    recs: list[str] = []

    if metrics.actuality_score < 0.5:
        recs.append("Попросить сотрудника подтвердить или обновить рабочий график.")

    if metrics.days_since_update > MAX_DAYS_WITHOUT_UPDATE:
        recs.append(
            f"График не обновлялся {metrics.days_since_update} дней — "
            "необходима актуализация."
        )

    if metrics.out_of_schedule_ratio > 0.3:
        recs.append(
            "Пересмотреть нагрузку и количество задач: "
            f"{metrics.meetings_out} из {metrics.meetings_total} встреч "
            "назначены вне рабочего времени."
        )

    if metrics.load_level > OVERLOAD_THRESHOLD:
        recs.append(
            f"Снизить количество встреч — уровень загрузки {metrics.load_level:.0%} "
            "превышает допустимый порог."
        )

    if metrics.timezone_conflict > 0:
        recs.append(
            f"Предложить обновить часовой пояс. {metrics.timezone_note}"
        )

    if metrics.hr_calendar_mismatch > 0.2:
        recs.append(
            "Проверить данные в HR-системе: события в календаре "
            "пересекаются с периодами отсутствия."
        )

    if metrics.has_exceptions:
        recs.append("Не назначать новые встречи в период действующих исключений.")

    if not recs:
        recs.append("Данные актуальны. Дополнительных действий не требуется.")

    return recs



class RiskAnalyticsService:

    def calculate_employee_metrics(
        self,
        employee: Employee,
        schedule: Schedule | None,
        events: Sequence[Event],
        exceptions: Sequence[ScheduleException],
        analysis_days: int = DEFAULT_ANALYSIS_DAYS,
    ) -> EmployeeRiskMetrics:
        now = datetime.now(tz=timezone.utc)
        period_start = now - timedelta(days=analysis_days)

        if schedule is None:
            days_since_update = MAX_DAYS_WITHOUT_UPDATE
            actuality_score = 0.0
        else:
            last_updated = _make_aware(schedule.updated_at)
            days_since_update = max(0, (now - last_updated).days)
            actuality_score = max(0.0, 1.0 - days_since_update / MAX_DAYS_WITHOUT_UPDATE)

        if schedule is None or not events:
            meetings_out = 0
            meetings_total = len(events)
            out_of_schedule_ratio = 0.0
        else:
            meetings_total = len(events)
            meetings_out = sum(
                1 for ev in events
                if _is_event_outside_schedule(ev.start_at, ev.end_at, schedule)
            )
            out_of_schedule_ratio = (
                meetings_out / meetings_total if meetings_total else 0.0
            )

        if schedule is None:
            hours_busy = _count_busy_hours(events)
            hours_work = analysis_days * 8.0
        else:
            hours_busy = _count_busy_hours(events)
            hours_work = _count_working_hours(period_start, now, schedule)

        load_level = hours_busy / hours_work if hours_work > 0 else 0.0

        if schedule is None:
            timezone_conflict, timezone_note = 0.0, ""
        else:
            timezone_conflict, timezone_note = _detect_timezone_conflict(
                events, schedule
            )

        if schedule is None:
            hr_calendar_mismatch = 0.0
        else:
            hr_calendar_mismatch = _detect_hr_calendar_mismatch(
                schedule, events, exceptions
            )

        li_clamped = min(load_level, 1.0)
        integral_risk = (
            W1_ACTUALITY * (1.0 - actuality_score)
            + W2_CONFLICTS * out_of_schedule_ratio
            + W3_LOAD * li_clamped
            + W4_TIMEZONE * timezone_conflict
            + W5_HR_MISMATCH * hr_calendar_mismatch
        )
        integral_risk = round(min(integral_risk, 1.0), 4)

        today = date.today()
        active_exceptions = [
            exc.type.value
            for exc in exceptions
            if exc.start_date <= today <= exc.end_date
        ]
        has_exceptions = bool(active_exceptions)

        metrics = EmployeeRiskMetrics(
            employee_id=employee.id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            patronymic=getattr(employee, "patronymic", None),
            actuality_score=round(actuality_score, 4),
            days_since_update=days_since_update,
            out_of_schedule_ratio=round(out_of_schedule_ratio, 4),
            meetings_out=meetings_out,
            meetings_total=meetings_total,
            load_level=round(load_level, 4),
            hours_busy=round(hours_busy, 2),
            hours_work=round(hours_work, 2),
            timezone_conflict=timezone_conflict,
            timezone_note=timezone_note,
            hr_calendar_mismatch=round(hr_calendar_mismatch, 4),
            integral_risk=integral_risk,
            active_exceptions=active_exceptions,
            has_exceptions=has_exceptions,
            time_zone=schedule.time_zone if schedule else "—",
            work_format=schedule.work_format.value if schedule else "—",
        )
        metrics.recommendations = _build_recommendations(metrics)
        return metrics

    def calculate_team_summary(
        self,
        metrics_list: list[EmployeeRiskMetrics],
    ) -> TeamRiskSummary:
        return TeamRiskSummary(
            employees=metrics_list,
            total_employees=len(metrics_list),
            outdated_count=sum(1 for m in metrics_list if m.actuality_score < 0.5),
            overloaded_count=sum(
                1 for m in metrics_list if m.load_level > OVERLOAD_THRESHOLD
            ),
            tz_conflict_count=sum(
                1 for m in metrics_list if m.timezone_conflict > 0
            ),
            high_risk_count=sum(1 for m in metrics_list if m.integral_risk > 0.6),
        )