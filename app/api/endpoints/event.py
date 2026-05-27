from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_current_user,
    get_user_with_roles,
    get_event_service,
)
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.event import (
    Event as EventSchema,
    EventCreate as EventCreateSchema,
    EventUpdate as EventUpdateSchema,
)
from app.schemas.employee import Employee as EmployeeSchema
from app.services import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=list[EventSchema])
async def get_all_events(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> list[EventSchema]:
    """
    Получение всех событий для любой роли.
    "hr" получает все, "manager" только те, в которых участвует
    хотя бы один сотрудник из его команд, "employee" только свои.
    """
    return await event_service.get_all(current_user)


@router.get("/me", response_model=list[EventSchema])
async def get_my_events(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> list[EventSchema]:
    """
    Получение собственных событий для любой роли.
    """
    return await event_service.get_all_by_user(current_user)


@router.get("/{id}", response_model=EventSchema)
async def get_event_by_id(
    id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventSchema:
    """
    Получение события по ID для любой роли.
    "hr" может получить любое, "manager" только если в нём есть
    сотрудник из его команд, "employee" только своё.
    """
    return await event_service.get_by_id(id, current_user)


@router.get("/{id}/employees", response_model=list[EmployeeSchema])
async def get_employees_by_event_id(
    id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> list[EmployeeSchema]:
    """
    Получение участников события по ID события.
    "hr" видит всех, "manager" только сотрудников из своих команд,
    "employee" всех сотрудников из своей команды участвующих в событии.
    """
    return await event_service.get_employees_by_event_id(id, current_user)


@router.post("/", response_model=EventSchema, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventSchema:
    """
    Создание события для ролей "manager", "hr".
    "hr" может создать для любого сотрудника,
    "manager" только для сотрудников из своих команд.
    """
    return await event_service.create(event, current_user)


@router.put("/{id}", response_model=EventSchema)
async def update_event(
    id: int,
    event: EventUpdateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventSchema:
    """
    Обновление события для ролей "manager", "hr".
    "hr" может обновить любое, "manager" только если в нём есть
    сотрудник из его команд.
    """
    return await event_service.update(id, event, current_user)


@router.post(
    "/{event_id}/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def add_employee_to_event(
    event_id: int,
    employee_id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> None:
    """
    Добавление сотрудника к событию.
    "hr" может добавить любого, "manager" только из своих команд.
    """
    await event_service.add_employee(event_id, employee_id, current_user)


@router.delete(
    "/{event_id}/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_employee_from_event(
    event_id: int,
    employee_id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> None:
    """
    Удаление сотрудника из события.
    "hr" может удалить любого, "manager" только из своих команд.
    """
    await event_service.remove_employee(event_id, employee_id, current_user)
