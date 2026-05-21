from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, SecretStr, ConfigDict

from app.models.user import Role


# Создание


class UserCreate(BaseModel):
    email: Annotated[
        EmailStr,
        Field(
            max_length=255,
            description="Электронная почта пользователя, до 255 символов",
        ),
    ]
    password: Annotated[
        str, Field(max_length=255, description="Пароль, до 255 символов")
    ]


class UserFullCreate(UserCreate):
    role: Annotated[
        Role, Field(description="Роль пользователя: manager, HR или employee")
    ]


# Обновление


class UserUpdate(BaseModel):
    email: Annotated[
        EmailStr | None,
        Field(
            max_length=255,
            description="Электронная почта пользователя, до 255 символов",
        ),
    ]
    role: Annotated[
        Role | None, Field(description="Роль пользователя: manager, HR или employee")
    ]


# Ответ


class User(BaseModel):
    id: Annotated[int, Field(description="Уникалльный индентификатор пользователя")]
    email: Annotated[str, Field(description="Электронная почта пользователя")]
    role: Annotated[Role, Field(description="Роль пользователя")]
    is_active: Annotated[bool, Field(description="Активность пользователя")]

    model_config = ConfigDict(from_attributes=True)
