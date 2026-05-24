from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_current_user,
    get_user_with_roles,
    get_employee_service,
)
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.employee import (
    Employee as EmployeeSchema,
    EmployeeCreate as EmployeeCreateSchema,
    EmployeeUpdate as EmployeeUpdateSchema,
)
from app.services import EmployeeService


router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[EmployeeSchema])
async def get_all_employees(
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> list[EmployeeSchema]:
    """
    Получение всех данных сотрудников для ролей "manager", "HR".
    "HR" просматривает всех сотрудников, "manager" только тех, кто
    а его командах.
    """
    return await employee_service.get_all(current_user)


@router.get("/me", response_model=EmployeeSchema)
async def get_my_employee(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeSchema:
    """
    Получение собственных данных.
    """
    return await employee_service.get_by_user(current_user)


@router.get("/{id}", response_model=EmployeeSchema)
async def get_employee_by_id(
    id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeSchema:
    """
    Получение данных сотрудника по ID для ролей "manager", "HR".
    "HR" может просмотреть любого сотрудника, "manager" только тех, кто
    в его командах.
    """
    return await employee_service.get_by_id(id, current_user)


@router.post("/", response_model=EmployeeSchema, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: EmployeeCreateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeSchema:
    """
    Добавление данных сотрудника для ролей "manager", "HR".
    "HR" может добавить любого сотрудника, "manager" только в
    свою команду.
    """
    return await employee_service.create(employee, current_user)


@router.put("/", response_model=EmployeeSchema)
async def update_employee(
    id: int,
    employee: EmployeeUpdateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    employee_service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeSchema:
    """
    Обновление данных сотрудника для ролей "manager", "HR".
    "HR" может поменять данные любого сотрудника, "manager" только тех,
    кто в его команде.
    """
    return await employee_service.update(id, employee, current_user)
