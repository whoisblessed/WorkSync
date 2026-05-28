from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Annotated


class MeetingSuggestRequest(BaseModel):
    employee_ids: Annotated[
        list[int],
        Field(
            min_length=2,
            description="ID сотрудников (employee.id), которых нужно собрать на встречу",
        ),
    ]
    duration_minutes: Annotated[
        int,
        Field(
            default=60,
            ge=15,
            le=480,
            description="Длительность встречи в минутах",
        ),
    ] = 60
    days_ahead: Annotated[
        int,
        Field(
            default=7,
            ge=1,
            le=30,
            description="Сколько дней вперёд искать окна",
        ),
    ] = 7


class UnavailableReason(BaseModel):
    employee_id: Annotated[int, Field(description="ID недоступного сотрудника")]
    full_name: Annotated[str, Field(description="ФИО сотрудника")]
    reason: Annotated[
        str,
        Field(
            description=(
                "Причина недоступности: "
                "'vacation' | 'sick_leave' | 'personal' | 'business_trip' "
                "| 'event' | 'out_of_schedule'"
            )
        ),
    ]
    reason_label: Annotated[
        str,
        Field(
            description="Человекочитаемая причина, например 'Отпуск' или 'Занят: Планёрка'"
        ),
    ]


class MeetingSlot(BaseModel):
    date: Annotated[str, Field(description="Дата слота, YYYY-MM-DD")]
    hour_start: Annotated[
        int, Field(description="Час начала (в таймзоне запрашивающего)")
    ]
    hour_end: Annotated[
        int, Field(description="Час окончания (в таймзоне запрашивающего)")
    ]
    available_count: Annotated[
        int, Field(description="Сколько из запрошенных сотрудников доступны")
    ]
    total_count: Annotated[int, Field(description="Всего запрошенных сотрудников")]
    unavailable_employee_ids: Annotated[
        list[int],
        Field(description="ID недоступных сотрудников"),
    ]
    unavailable_reasons: Annotated[
        list[UnavailableReason],
        Field(description="Детальные причины недоступности каждого сотрудника"),
    ] = []
    warnings: Annotated[
        list[str],
        Field(
            description=(
                "Предупреждения для этого слота, например: "
                "'Иванов А.В. - Отпуск', 'Сидоров К.П. - Перегрузка', "
                "'Рекомендуется сократить встречу до 15 минут'"
            )
        ),
    ] = []


class MeetingSuggestResponse(BaseModel):
    slots: Annotated[
        list[MeetingSlot],
        Field(
            description="Топ-3 лучших окна для встречи, отсортированы по убыванию доступности"
        ),
    ]
    ai_explanation: Annotated[
        str,
        Field(description="AI-объяснение почему предложены именно эти слоты"),
    ]
