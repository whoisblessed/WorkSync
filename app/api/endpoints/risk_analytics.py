"""
Эндпоинты экрана «Конфликты и риски».

GET /api/risk-analytics/
    Таблица сотрудников с рассчитанными метриками.
    Query-параметры: period_days, department_id, sort_by, sort_desc, group_by

GET /api/risk-analytics/{employee_id}
    Детальные метрики одного сотрудника + рекомендации.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_user_with_roles
from app.models import User
from app.models.user import Role
from app.repositories.risk_analytics import RiskAnalyticsRepository
from app.services.risk_analytics import RiskAnalyticsService
from app.schemas.risk_analytics import (
    EmployeeRiskSchema,
    TeamRiskSummarySchema,
)
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ForbiddenException


router = APIRouter(prefix="/risk-analytics", tags=["risk-analytics"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


def get_risk_repo(session: DBSession) -> RiskAnalyticsRepository:
    return RiskAnalyticsRepository(session)


def get_risk_service() -> RiskAnalyticsService:
    return RiskAnalyticsService()


# ─── Вспомогательная функция сборки метрик ───────────────────────────────────

async def _build_metrics_list(
    repo: RiskAnalyticsRepository,
    service: RiskAnalyticsService,
    current_user: User,
    period_days: int,
    team_id: int | None,
) -> list:
    now = datetime.now(tz=timezone.utc)
    period_start = now - timedelta(days=period_days)

    # Определяем фильтр по команде/менеджеру
    manager_user_id = (
        current_user.id if current_user.role == Role.manager else None
    )

    employees = await repo.get_employees_with_relations(
        manager_user_id=manager_user_id,
        team_id=team_id,
    )

    metrics_list = []
    for emp in employees:
        schedule = await repo.get_schedule_for_employee(emp.id)
        events = await repo.get_events_for_employee_in_period(
            emp.id, period_start, now
        )
        exceptions = await repo.get_exceptions_for_employee(emp.id)

        m = service.calculate_employee_metrics(
            employee=emp,
            schedule=schedule,
            events=events,
            exceptions=exceptions,
            analysis_days=period_days,
        )
        metrics_list.append(m)

    return metrics_list


# ─── Эндпоинты ───────────────────────────────────────────────────────────────

ALLOWED_SORT_FIELDS = {
    "integral_risk",
    "actuality_score",
    "load_level",
    "out_of_schedule_ratio",
    "days_since_update",
}


@router.get(
    "/",
    response_model=TeamRiskSummarySchema,
    summary="Таблица рисков сотрудников",
    description=(
        "Возвращает список сотрудников с рассчитанными метриками риска "
        "неактуальности рабочего времени. "
        "Доступно для ролей: hr, manager, admin."
    ),
)
async def get_risk_table(
    current_user: Annotated[
        User, Depends(get_user_with_roles(Role.hr, Role.manager, Role.admin))
    ],
    repo: Annotated[RiskAnalyticsRepository, Depends(get_risk_repo)],
    service: Annotated[RiskAnalyticsService, Depends(get_risk_service)],
    period_days: int = Query(
        default=30, ge=1, le=365, description="Период анализа в днях"
    ),
    department_id: int | None = Query(
        default=None, description="Фильтр по ID команды"
    ),
    sort_by: str = Query(
        default="integral_risk",
        description="Поле сортировки: integral_risk | actuality_score | load_level | out_of_schedule_ratio | days_since_update",
    ),
    sort_desc: bool = Query(default=True, description="Сортировка по убыванию"),
) -> TeamRiskSummarySchema:
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = "integral_risk"

    metrics_list = await _build_metrics_list(
        repo, service, current_user, period_days, department_id
    )

    # Сортировка
    metrics_list.sort(
        key=lambda m: getattr(m, sort_by, 0),
        reverse=sort_desc,
    )

    summary = service.calculate_team_summary(metrics_list)

    # Конвертируем dataclass → Pydantic через dict
    return TeamRiskSummarySchema(
        employees=[
            EmployeeRiskSchema(**m.__dict__) for m in summary.employees
        ],
        total_employees=summary.total_employees,
        outdated_count=summary.outdated_count,
        overloaded_count=summary.overloaded_count,
        tz_conflict_count=summary.tz_conflict_count,
        high_risk_count=summary.high_risk_count,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeRiskSchema,
    summary="Детальные метрики риска одного сотрудника",
    description=(
        "Возвращает полные метрики и рекомендации для выбранного сотрудника. "
        "HR и admin видят любого сотрудника, manager — только своей команды, "
        "employee — только себя."
    ),
)
async def get_employee_risk(
    employee_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[RiskAnalyticsRepository, Depends(get_risk_repo)],
    service: Annotated[RiskAnalyticsService, Depends(get_risk_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> EmployeeRiskSchema:
    now = datetime.now(tz=timezone.utc)
    period_start = now - timedelta(days=period_days)

    # Загружаем сотрудников, доступных текущему пользователю
    manager_user_id = (
        current_user.id if current_user.role == Role.manager else None
    )
    employees = await repo.get_employees_with_relations(
        manager_user_id=manager_user_id
    )

    # Для роли employee — только свой профиль
    if current_user.role == Role.employee:
        employee = next((e for e in employees if e.user_id == current_user.id), None)
        if employee is None or employee.id != employee_id:
            raise ForbiddenException(
                "Доступ к метрикам другого сотрудника запрещён."
            )
    else:
        employee = next((e for e in employees if e.id == employee_id), None)

    if employee is None:
        raise NotFoundException(f"Сотрудник с ID {employee_id} не найден.")

    schedule = await repo.get_schedule_for_employee(employee.id)
    events = await repo.get_events_for_employee_in_period(
        employee.id, period_start, now
    )
    exceptions = await repo.get_exceptions_for_employee(employee.id)

    m = service.calculate_employee_metrics(
        employee=employee,
        schedule=schedule,
        events=events,
        exceptions=exceptions,
        analysis_days=period_days,
    )
    return EmployeeRiskSchema(**m.__dict__)