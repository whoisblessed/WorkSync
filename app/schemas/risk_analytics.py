from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


class EmployeeRiskSchema(BaseModel):
    employee_id: Annotated[int, Field(description="ID сотрудника")]
    first_name: Annotated[str, Field(description="Имя")]
    last_name: Annotated[str, Field(description="Фамилия")]
    patronymic: Annotated[str | None, Field(default=None, description="Отчество")]
    actuality_score: Annotated[
        float,
        Field(
            description="Показатель актуальности графика Ai = 1 - di/D, диапазон [0..1]"
        ),
    ]
    days_since_update: Annotated[
        int,
        Field(
            description="Кол-во дней с момента последнего обновления графика (di)"
        ),
    ]
    out_of_schedule_ratio: Annotated[
        float,
        Field(
            description="Доля встреч вне рабочего времени Ci = Mout/Mall, диапазон [0..1]"
        ),
    ]
    meetings_out: Annotated[
        int, Field(description="Кол-во встреч вне рабочего времени (Mout)")
    ]
    meetings_total: Annotated[
        int, Field(description="Всего встреч за период анализа (Mall)")
    ]
    load_level: Annotated[
        float,
        Field(
            description="Уровень загрузки Li = Hbusy/Hwork; >0.8 — перегрузка"
        ),
    ]
    hours_busy: Annotated[
        float, Field(description="Занятых часов за период (Hbusy)")
    ]
    hours_work: Annotated[
        float,
        Field(description="Рабочих часов по графику за период (Hwork)"),
    ]
    timezone_conflict: Annotated[
        float, Field(description="Признак конфликта часового пояса Zi (0 или 1)")
    ]
    timezone_note: Annotated[str, Field(default="", description="Описание конфликта TZ")]
    time_zone: Annotated[str, Field(description="Часовой пояс из расписания")]
    hr_calendar_mismatch: Annotated[
        float,
        Field(
            description="Расхождение HR-данных и календаря Hi, диапазон [0..1]"
        ),
    ]
    integral_risk: Annotated[
        float,
        Field(
            description="Интегральный риск неактуальности Ri = w1*(1-Ai)+w2*Ci+w3*Li+w4*Zi+w5*Hi, диапазон [0..1]"
        ),
    ]
    work_format: Annotated[
        str, Field(description="Формат работы: office / remote / hybrid")
    ]
    has_exceptions: Annotated[bool, Field(description="Есть ли активные исключения")]
    active_exceptions: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="Типы активных исключений: vacation, sick_leave, …",
        ),
    ]
    recommendations: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="Список рекомендаций для сотрудника",
        ),
    ]

    model_config = ConfigDict(from_attributes=True)


class TeamRiskSummarySchema(BaseModel):
    employees: Annotated[
        list[EmployeeRiskSchema],
        Field(description="Метрики по каждому сотруднику (строки таблицы)"),
    ]
    total_employees: Annotated[int, Field(description="Всего сотрудников")]
    outdated_count: Annotated[
        int, Field(description="Сотрудников с устаревшим графиком (Ai < 0.5)")
    ]
    overloaded_count: Annotated[
        int, Field(description="Перегруженных сотрудников (Li > 0.8)")
    ]
    tz_conflict_count: Annotated[
        int, Field(description="Сотрудников с конфликтом часового пояса")
    ]
    high_risk_count: Annotated[
        int, Field(description="Сотрудников с высоким риском (Ri > 0.6)")
    ]


class RiskFilterParams(BaseModel):
    period_days: Annotated[
        int,
        Field(
            default=30,
            ge=1,
            le=365,
            description="Период анализа в днях (окно анализа событий)",
        ),
    ]
    department_id: Annotated[
        int | None,
        Field(default=None, description="ID команды (None = все доступные)"),
    ]
    sort_by: Annotated[
        str,
        Field(
            default="integral_risk",
            description="Поле сортировки: integral_risk | actuality_score | load_level | out_of_schedule_ratio | days_since_update",
        ),
    ]
    sort_desc: Annotated[
        bool, Field(default=True, description="Сортировка по убыванию")
    ]
    group_by: Annotated[
        str | None,
        Field(
            default=None,
            description="Группировка: work_format | time_zone | has_exceptions",
        ),
    ]