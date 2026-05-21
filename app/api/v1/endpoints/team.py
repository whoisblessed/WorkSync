from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, user_require_roles, get_team_service
from app.models import User as UserModel
from app.models.user import Role
from app.shemas.team import (
    Team as TeamSchema,
    TeamCreate as TeamCreateSchema,
    TeamUpdate as TeamUpdateSchema,
)
from app.services import TeamService


router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamSchema])
async def get_all(
    current_user: Annotated[
        UserModel, Depends(user_require_roles(Role.manager, Role.hr))
    ],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> list[TeamSchema]:
    """
    Получение всех команд для ролей "employee", "manager", "HR".
    "HR" доступны все команды, "manager" только свои.
    """
    return await team_service.get_all(current_user)


@router.get("/me", response_model=TeamSchema)
async def get_my(
    current_user: Annotated[UserModel, Depends(user_require_roles(Role.employee))],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> TeamSchema:
    """
    Получение своей команды для роли "employee".
    """
    return await team_service.get_by_user(current_user)


@router.get("/{id}", response_model=TeamSchema)
async def get_by_id(
    id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> list[TeamSchema]:
    """
    Получение команды по id для ролей "employee", "manager", "HR".
    "HR" доступны все команды, "manager" только свои,
    "employee" только та, в которой он состоит.
    """
    return await team_service.get_by_id(id, current_user)


@router.post("/", response_model=TeamSchema, status_code=status.HTTP_201_CREATED)
async def create(
    team: TeamCreateSchema,
    current_user: Annotated[
        UserModel, Depends(user_require_roles(Role.manager, Role.hr))
    ],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> TeamSchema:
    """
    Создание команды для ролей "manager", "HR".
    "HR" может создать команду с любым руководителем, "manager" только для себя.
    """
    return await team_service.create(team, current_user)


@router.put("/{id}", response_model=TeamSchema)
async def update(
    id: int,
    team: TeamUpdateSchema,
    current_user: Annotated[
        UserModel, Depends(user_require_roles(Role.manager, Role.hr))
    ],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> TeamSchema:
    """
    Обновление команды для ролей "manager", "HR".
    "HR" может обновлять любые команды, "manager" только свои.
    """
    return await team_service.update(id, team, current_user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate(
    id: int,
    current_user: Annotated[
        UserModel, Depends(user_require_roles(Role.manager, Role.hr))
    ],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> None:
    """
    Деактивация команды для ролей "manager", "HR".
    "HR" может деактивировать любые команды, "manager" только свои.
    """
    return await team_service.deactivate(id, current_user)


@router.patch("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def activate(
    id: int,
    current_user: Annotated[
        UserModel, Depends(user_require_roles(Role.manager, Role.hr))
    ],
    team_service: Annotated[TeamService, Depends(get_team_service)],
) -> None:
    """
    Активация команды для ролей "manager", "HR".
    "HR" может деактивировать любые команды, "manager" только свои.
    """
    return await team_service.activate(id, current_user)
