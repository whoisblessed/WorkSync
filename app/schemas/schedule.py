from typing import Annotated
from datetime import datetime, time

from app.models.schedule import WorkFormat

from pydantic import BaseModel, Field, ConfigDict, field_validator


# Базовые поля


class BaseSchedule(BaseModel):
    work_days: Annotated[
        list[int], Field(description="Дни, в которые работает сотрудник")
    ]
    time_zone: Annotated[str, Field(description="Часовой пояс сотрудника")]
    work_format: Annotated[WorkFormat, Field(description="Формат работы сотрудника")]
    start_at: Annotated[time, Field(description="Начало работы сотрудника")]
    end_at: Annotated[time, Field(description="Конец работы сотрудника")]

    @field_validator("work_days", mode="after")
    @classmethod
    def validate_work_days(cls, work_days: list[int]) -> list[int]:
        if not work_days:
            raise ValueError("Значение не передано")

        work_days.sort()

        if not all([1 <= work_day <= 7 for work_day in work_days]):
            raise ValueError("В список передано значение вне диапазона от 1 до 7")
        if len(work_days) != len(set(work_days)):
            raise ValueError("Введены повторяющиеся дни")

        return work_days


# Создание


class ScheduleCreate(BaseSchedule):
    employee_id: Annotated[int, Field("ID сотрудника, которому принадлежит график")]


# Обновление


class ScheduleUpdate(BaseSchedule):
    pass


# Ответ


class Schedule(BaseModel):
    id: Annotated[int, Field(description="Уникальный идентификатор поля")]
    work_days: Annotated[
        list[int], Field(description="Дни, в которые работает сотрудник")
    ]
    time_zone: Annotated[str, Field(description="Часовой пояс сотрудника")]
    work_format: Annotated[WorkFormat, Field(description="Формат работы сотрудника")]
    start_at: Annotated[time, Field(description="Начало работы сотрудника")]
    end_at: Annotated[time, Field(description="Конец работы сотрудника")]
    updated_at: Annotated[
        datetime, Field(description="Время последнего обновления графика сотрудника")
    ]
    is_active: Annotated[bool, Field(description="Активность графика сотрудника")]
    employee_id: Annotated[
        int, Field(description="ID сотрудника, которому принадлежит график")
    ]

    model_config = ConfigDict(from_attributes=True)
