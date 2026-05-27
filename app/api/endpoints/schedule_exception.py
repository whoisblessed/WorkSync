from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_current_user,
    get_user_with_roles,
    get_schedule_exception_service,
)
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.schedule_exception import (
    ScheduleException as ScheduleExceptionSchema,
    ScheduleExceptionCreate as ScheduleExceptionCreateSchema,
    ScheduleExceptionUpdate as ScheduleExceptionUpdateSchema,
)
from app.services import ScheduleExceptionService


router = APIRouter(prefix="/schedule_exceptions", tags=["schedule_exceptions"])


@router.get("/", response_model=list[ScheduleExceptionSchema])
async def get_all_schedule_exceptions(
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    schedule_exception_service: Annotated[
        ScheduleExceptionService, Depends(get_schedule_exception_service)
    ],
) -> list[ScheduleExceptionSchema]:
    """
    Получение всех временных исключений для любой роли.
    "hr" просматривает все, "manager" только сотрудников, в чьей команде он состоит
    "employee" только свои.
    """
    return await schedule_exception_service.get_all(current_user)


@router.get("/{id}", response_model=ScheduleExceptionSchema)
async def get_schedule_exception_by_id(
    id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    schedule_exception_service: Annotated[
        ScheduleExceptionService, Depends(get_schedule_exception_service)
    ],
) -> ScheduleExceptionSchema:
    """
    Получение временного исключения по id для любой роли.
    "hr" просматривает все, "manager" только сотрудников, в чьих командах он состоит
    "employee" только свои.
    """
    return await schedule_exception_service.get_by_id(id, current_user)


@router.post(
    "/", response_model=ScheduleExceptionSchema, status_code=status.HTTP_201_CREATED
)
async def create_schedule_exception(
    schedule_exception: ScheduleExceptionCreateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    schedule_exception_service: Annotated[
        ScheduleExceptionService, Depends(get_schedule_exception_service)
    ],
) -> ScheduleExceptionSchema:
    """
    Создание временного исключения для любой роли.
    "hr" может создать для всех, "manager" только для сотрудника в его командах
    "employee" только свои.
    """
    return await schedule_exception_service.create(schedule_exception, current_user)


@router.put("/", response_model=ScheduleExceptionSchema)
async def update_schedule_exception(
    id: int,
    schedule_exception: ScheduleExceptionUpdateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    schedule_exception_service: Annotated[
        ScheduleExceptionService, Depends(get_schedule_exception_service)
    ],
) -> ScheduleExceptionSchema:
    """
    Оьновление временного исключения по id для любой роли.
    "hr" может обновлять для всех, "manager" только для сотрудника в его командах
    "employee" только свои.
    """
    return await schedule_exception_service.update(id, schedule_exception, current_user)
