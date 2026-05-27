from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.api.dependencies import (
    get_current_user,
    get_user_with_roles,
    get_schedule_service,
)
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.schedule import (
    Schedule as ScheduleSchema,
    ScheduleCreate as ScheduleCreateSchema,
    ScheduleUpdate as ScheduleUpdateSchema,
)
from app.services import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/", response_model=list[ScheduleSchema])
async def get_all_schedules(
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    schedule_service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> list[ScheduleSchema]:
    """
    Получение всех графиков для ролей "manager", "hr".
    "hr" получает все графики, "manager" графики только тех,
    кто состоит в его командах.
    """
    return await schedule_service.get_all(current_user)


@router.get("/me", response_model=ScheduleSchema)
async def get_my_schedule(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    schedule_service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleSchema:
    """
    Получение собственного графика.
    """
    return await schedule_service.get_by_user(current_user)


@router.get("/{id}", response_model=ScheduleSchema)
async def get_schedule_by_id(
    id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    schedule_service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleSchema:
    """
    Получение всех графика по его ID для ролей "manager", "hr".
    "hr" может получить все графики, "manager" графики только тех,
    кто состоит в его командах.
    """
    return await schedule_service.get_by_id(id, current_user)


@router.post("/", response_model=ScheduleSchema, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ScheduleCreateSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    schedule_service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleSchema:
    """
    Создание графика дял всех ролей.
    "hr" может создавать график для всех,
    "manager" для тех,кто в его командах, "employee" для себя.
    Создать график можно только для сотрудника с ролью "employee".
    """
    return await schedule_service.create(schedule, current_user)


@router.put("/{id}", response_model=ScheduleSchema)
async def update_schedule(
    id: int,
    schedule: ScheduleUpdateSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    schedule_service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleSchema:
    """
    Обновление графика дял всех ролей.
    "hr" может обновлять график для всех,
    "manager" для тех,кто в его командах, "employee" для себя.
    Создать график можно только для сотрудника с ролью "employee".
    """
    return await schedule_service.update(id, schedule, current_user)
