from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_current_user,
    get_user_with_roles,
    get_profile_service,
)
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.profile import Profile as ProfileSchema
from app.services import ProfileService


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/", response_model=list[ProfileSchema])
async def get_all_profiles(
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> list[ProfileSchema]:
    """
    Получение всех профилей.
    "hr" получает все, "manager" только из своих команд.
    """
    return await profile_service.get_all(current_user)


@router.get("/me", response_model=ProfileSchema)
async def get_my_profile(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileSchema:
    """
    Получение собственного профиля для любой роли.
    """
    return await profile_service.get_profile(current_user)


@router.get("/{user_id}", response_model=ProfileSchema)
async def get_profile_by_id(
    user_id: int,
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileSchema:
    """
    Получение профиля по user_id.
    "hr" может получить любой, "manager" только из своих команд.
    """
    return await profile_service.get_by_id(user_id, current_user)
