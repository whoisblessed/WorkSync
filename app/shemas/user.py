from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.models.user import Role


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(max_length=255, description="Электронная почта пользователя, до 255 символов")]
    hashed_password: Annotated[str, Field(description="Захешированный пароль")]
    role: Annotated[Role, Field(description="Роль пользователя: manager, HR или employee")]
    
    
class UserUpdate(BaseModel):
    


class User(BaseModel):
    id: Annotated[int, Field(description="Уникалльный индентификатор пользователя")]
    email: Annotated[str, Field(description="Электронная почта пользователя")]
    hashed_password: Annotated[str, Field(description="Захешированный пароль")]
    role: Annotated[Role, Field(description="Роль пользователя")]
    is_active: Annotated[bool, Field(description="Активность пользователя")]
    
    model_config = ConfigDict(from_attributes=True)