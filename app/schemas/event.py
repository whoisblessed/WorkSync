from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.event import EventType


class EventCreate(BaseModel):
    type: Annotated[EventType, Field(description="Тип события")]
    title: Annotated[str, Field(max_length=150, description="Название события")]
    description: Annotated[str, Field(max_length=500, description="Описание события")]
    start_at: Annotated[datetime, Field(description="Дата и время начала события")]
    end_at: Annotated[datetime, Field(description="Дата и время конца события")]

    @model_validator(mode="after")
    def validate_dates(self) -> EventCreate:
        if self.end_at <= self.start_at:
            raise ValueError("Дата конца не может быть раньше или равна дате начала")
        return self


class EventUpdate(EventCreate):
    pass


class Event(BaseModel):
    id: Annotated[int, Field(description="Уникальный идентификатор события")]
    type: Annotated[EventType, Field(description="Тип события")]
    title: Annotated[str, Field(description="Название события")]
    description: Annotated[str, Field(description="Описание события")]
    start_at: Annotated[datetime, Field(description="Дата и время начала события")]
    end_at: Annotated[datetime, Field(description="Дата и время конца события")]
    is_active: Annotated[bool, Field(description="Активность события")]

    model_config = ConfigDict(from_attributes=True)
