from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


# Базовые поля


class EmployeeBase(BaseModel):
    first_name: Annotated[
        str, Field(max_length=255, description="Имя сотрудника, до 255 символов")
    ]
    last_name: Annotated[
        str, Field(max_length=255, description="Фамилия сотрудника, до 255 символов")
    ]
    team_id: Annotated[
        int, Field(description="ID команды, в которой состоит сотрудник")
    ]


# Создание


class EmployeeCreate(EmployeeBase):
    team_id: Annotated[
        int, Field(description="ID команды, в которой состоит сотрудник")
    ]


# Обновление


class EmployeeUpdate(EmployeeBase):
    pass


# Ответ


class Employee(BaseModel):
    id: Annotated[int, Field(description="Уникальный идентификатор профиля сотрудника")]
    first_name: Annotated[str, Field(description="Имя сотрудника")]
    last_name: Annotated[str, Field(description="Фамилия сотрудника")]
    is_active: Annotated[bool, Field(description="Активность профиля сотрудника")]
    user_id: Annotated[
        int, Field(description="ID пользователя, на которого зарегистрирован профиль")
    ]
    team_id: Annotated[
        int, Field(description="ID команды, в которой состоит сотрудник")
    ]

    model_config = ConfigDict(from_attributes=True)
