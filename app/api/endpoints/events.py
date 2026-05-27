from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_user_with_roles, get_event_service
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.events import (
    Event as EventSchema,
    EventCreate as EventCreateSchema,
    EventUpdate as EventUpdateSchema,
)
from app.services.events import EventService


router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=list[EventSchema])
async def get_all_events(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> list[EventSchema]:
    """
    Получение списка событий.
    - **hr**: все события.
    - **manager**: только события, в которых участвуют сотрудники его команды.
    - **employee**: только свои события.
    """
    return await event_service.get_all(current_user)


@router.get("/{id}", response_model=EventSchema)
async def get_event_by_id(
    id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventSchema:
    """
    Получение события по ID.
    Доступ аналогичен правилам из GET /.
    """
    return await event_service.get_by_id(id, current_user)


@router.post("/", response_model=EventSchema, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreateSchema,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventSchema:
    """
    Создание события (доступно manager и hr).
    - **manager**: может добавлять встречи только сотрудникам из своего отдела.
    - **hr**: может добавлять встречи любым сотрудникам.
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
    Обновление события (manager и hr).
    manager может обновлять только события своих сотрудников.
    """
    return await event_service.update(id, event, current_user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_event(
    id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> None:
    """
    Деактивация события (manager и hr).
    manager может деактивировать только события своих сотрудников.
    """
    return await event_service.deactivate(id, current_user)


@router.patch("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def activate_event(
    id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> None:
    """
    Активация события (manager и hr).
    manager может активировать только события своих сотрудников.
    """
    return await event_service.activate(id, current_user)