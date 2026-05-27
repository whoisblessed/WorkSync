from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class EmployeeEventCreate(BaseModel):
    employee_id: Annotated[int, Field(description="ID сотрудника")]
    event_id: Annotated[int, Field(description="ID события")]


class EmployeeEvent(EmployeeEventCreate):
    model_config = ConfigDict(from_attributes=True)
