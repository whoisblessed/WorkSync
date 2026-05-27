from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.event import EventType


# Создание


class EventCreate(BaseModel):
    type: Annotated[EventType, Field(description="Тип события: task или meeting")]
    title: Annotated[str, Field(max_length=150, description="Название события")]
    description: Annotated[
        str, Field(max_length=500, description="Описание события")
    ]
    start_at: Annotated[datetime, Field(description="Дата и время начала события")]
    end_at: Annotated[datetime, Field(description="Дата и время конца события")]
    employee_ids: Annotated[
        list[int], Field(min_length=1, description="Список ID сотрудников")
    ]

    @model_validator(mode="after")
    def validate_dates(self) -> "EventCreate":
        if self.end_at <= self.start_at:
            raise ValueError("Дата конца события должна быть позже даты начала")
        return self


# Обновление


class EventUpdate(BaseModel):
    type: Annotated[EventType, Field(description="Тип события: task или meeting")]
    title: Annotated[str, Field(max_length=150, description="Название события")]
    description: Annotated[
        str, Field(max_length=500, description="Описание события")
    ]
    start_at: Annotated[datetime, Field(description="Дата и время начала события")]
    end_at: Annotated[datetime, Field(description="Дата и время конца события")]

    @model_validator(mode="after")
    def validate_dates(self) -> "EventUpdate":
        if self.end_at <= self.start_at:
            raise ValueError("Дата конца события должна быть позже даты начала")
        return self


# Ответ


class EventEmployee(BaseModel):
    id: int
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class Event(BaseModel):
    id: Annotated[int, Field(description="Уникальный идентификатор события")]
    type: Annotated[EventType, Field(description="Тип события")]
    title: Annotated[str, Field(description="Название события")]
    description: Annotated[str, Field(description="Описание события")]
    start_at: Annotated[datetime, Field(description="Дата и время начала")]
    end_at: Annotated[datetime, Field(description="Дата и время конца")]
    is_active: Annotated[bool, Field(description="Активность события")]
    employees: Annotated[
        list[EventEmployee], Field(description="Список участников события")
    ]

    model_config = ConfigDict(from_attributes=True)