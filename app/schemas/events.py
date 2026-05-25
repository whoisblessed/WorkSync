from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.event import EventType



class EventCreate(BaseModel):
    type: Annotated[
        EventType,
        Field(description="Тип события"), #'задача' или 'встреча'
    ]
    title: Annotated[
        str,
        Field(max_length=150, description="Название события"),
    ]
    description: Annotated[
        str,
        Field(max_length=500, description="Описание события"),
    ]
    start_at: Annotated[
        datetime,
        Field(description="Время начала события"), # (ISO формат с часовым поясом)
    ]
    end_at: Annotated[
        datetime,
        Field(description="Время окончания события"), # (ISO формат с часовым поясом)
    ]
    employee_ids: Annotated[
        list[int],
        Field(
            description="Список ID сотрудников, участвующих в событии",
            min_length=1,
        ),
    ]


class EventUpdate(BaseModel):
    type: Annotated[
        EventType | None,
        Field(default=None, description="Тип события"), # 'задача' или 'встреча'
    ] = None
    title: Annotated[
        str | None,
        Field(default=None, max_length=150, description="Название события"),
    ] = None
    description: Annotated[
        str | None,
        Field(default=None, max_length=500, description="Описание события"),
    ] = None
    start_at: Annotated[
        datetime | None,
        Field(default=None, description="Время начала события"), # (ISO формат с часовым поясом)
    ] = None
    end_at: Annotated[
        datetime | None,
        Field(default=None, description="Время окончания события"), # (ISO формат с часовым поясом)
    ] = None
    employee_ids: Annotated[
        list[int] | None,
        Field(default=None, description="Список ID сотрудников", min_length=1),
    ] = None



class Event(BaseModel):
    id: Annotated[int, Field(description="id события")]
    type: Annotated[EventType, Field(description="Тип события")]
    title: Annotated[str, Field(description="Название события")]
    description: Annotated[str, Field(description="Описание события")]
    start_at: Annotated[datetime, Field(description="Время начала события")]
    end_at: Annotated[datetime, Field(description="Время окончания события")]
    is_active: Annotated[bool, Field(description="Активность события")]
    employee_ids: Annotated[
        list[int], Field(description="ID сотрудников-участников")
    ]

    model_config = ConfigDict(from_attributes=True)
