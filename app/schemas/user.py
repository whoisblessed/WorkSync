from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr


class Role(str, Enum):
    manager = "manager"
    hr = "HR"
    employee = "employee"


class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    role: Role


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    employee: EmployeeResponse | None = None

    model_config = ConfigDict(from_attributes=True)