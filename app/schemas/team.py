from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


# Создание


class TeamCreate(BaseModel):
    name: Annotated[str, Field(description="Название команды, до 255 символов")]
    description: Annotated[
        str | None, Field(description="Описание команды, до 500 символов")
    ]
    manager_id: Annotated[int, Field(description="ID менеджера команды")]


# Обновление


class TeamUpdate(TeamCreate):
    pass


# Ответ


class Team(BaseModel):
    id: Annotated[int, Field(description="Уникальный идентификатор команды")]
    name: Annotated[str, Field(description="Название команды")]
    description: Annotated[str | None, Field(description="Описание команды")]
    is_active: Annotated[bool, Field(description="Активность команды")]
    manager_id: Annotated[int, Field(description="ID менеджера команды")]

    model_config = ConfigDict(from_attributes=True)
