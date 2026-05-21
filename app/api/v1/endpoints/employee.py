from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_current_user,
    user_require_roles,
    get_employee_service,
)
from app.models import User as UserModel
from app.models.user import Role
from app.shemas.employee import (
    Employee as EmployeeSchema,
    EmployeeCreate as EmployeeCreateSchema,
    EmployeeUpdate as EmployeeUpdateSchema,
)
from app.services import EmployeeService


router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[EmployeeSchema])
async def get_all(
    current_user: Annotated[
        UserModel, Depends(user_require_roles(Role.manager, Role.hr))
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> list[EmployeeSchema]:
    """
    Получение всех данных сотрудников для ролей "manager", "HR".
    "HR" просматривает всех сотрудников, "manager" только тех, кто
    а его командах.
    """
    return await employee_service


@router.get("/me", response_model=EmployeeSchema)
async def get_me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeSchema:
    """
    Получение собственных данных.
    """
    return await employee_service


@router.get("/{id}", response_model=EmployeeSchema)
async def get_by_id(
    id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeSchema:
    """
    Получение данных сотрудника для ролей "manager", "HR".
    "HR" может просмотреть любого сотрудника, "manager" только тех, кто
    в его командах.
    """
    return await employee_service
