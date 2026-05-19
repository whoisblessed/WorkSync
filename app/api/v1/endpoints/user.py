from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, user_require_roles, get_user_service
from app.models import User as UserModel
from app.models.user import Role
from app.shemas.user import (
    User as UserSchema,
    UserCreate as UserCreateSchema,
    UserUpdate as UserUpdateSchema,
)
from app.services import UserService


router = APIRouter(prefix="/users")


@router.get("/{id}", response_model=UserSchema)
async def get_user_by_id(
    id: int,
    _: Annotated[UserModel, Depends(user_require_roles(Role.hr, Role.manager))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    """Получить пользователя"""
    return await user_service.get_by_id(id)


@router.post("/", response_model=UserSchema)
async def register(
    user: UserCreateSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    return await user_service.register(user, current_user)


@router.patch("/", response_model=UserSchema)
async def update(
    user: UserUpdateSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    return await user_service.update(user, current_user)


@router.delete("/{id}", response_model=UserSchema)
async def deactivate(
    id: int,
    _: Annotated[UserModel, Depends(user_require_roles(Role.hr, Role.manager))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    return await user_service.deactivate_by_id(id)


@router.delete("/{id}", response_model=UserSchema)
async def activate(
    id: int,
    _: Annotated[UserModel, Depends(user_require_roles(Role.hr, Role.manager))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    return await user_service.activate_by_id(id)
