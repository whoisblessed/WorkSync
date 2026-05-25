from typing import Annotated
from datetime import date

from app.models.schedule_exception import ScheduleExceptionType

from pydantic import BaseModel, Field, ConfigDict


class BaseScheduleException(BaseModel):
    type: Annotated[
        ScheduleExceptionType, Field(description="Тип временного исключения")
    ]
    description: Annotated[
        str | None,
        Field(
            max_length=500,
            description="Описание временного исключения, до 500 символов",
        ),
    ]
    start_date: Annotated[
        date, Field(Field(description="Дата начала временного исключения"))
    ]
    end_date: Annotated[
        date, Field(Field(description="Дата конца временного исключения"))
    ]


class ScheduleExceptionCreate(BaseScheduleException):
    employee_id: Annotated[
        int,
        Field(description="ID сотрудника, которому принадлежит временное исключение"),
    ]


class ScheduleExceptionUpdate(BaseScheduleException):
    pass


class ScheduleException(BaseModel):
    id: Annotated[
        int, Field(description="Уникальный идентификатор временного исключения")
    ]
    type: Annotated[
        ScheduleExceptionType, Field(description="Тип временного исключения")
    ]
    description: Annotated[
        str | None, Field(description="Описание временного исключения")
    ]
    start_date: Annotated[
        date, Field(Field(description="Дата начала временного исключения"))
    ]
    end_date: Annotated[
        date, Field(Field(description="Дата конца временного исключения"))
    ]
    is_active: Annotated[bool, Field(description="Активность временного исключения")]

    employee_id: Annotated[
        int,
        Field(description="ID сотрудника, которому принадлежит временное исключение"),
    ]
