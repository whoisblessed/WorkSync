from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_user_with_roles, get_user_service
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.user import (
    User as UserSchema,
    UserCreate as UserCreateSchema,
    UserFullCreate as UserFullCreateSchema,
    UserUpdate as UserUpdateSchema,
)
from app.services import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
async def get_my_user(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserSchema:
    """
    Получение собственного пользователя.
    """
    return current_user


@router.get("/{id}", response_model=UserSchema)
async def get_user_by_id(
    id: int,
    _: Annotated[UserModel, Depends(get_user_with_roles(Role.hr))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    """
    Получение пользователя по его id. Доступно роли "HR".
    """
    return await user_service.get_by_id(id)


@router.post(
    "/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED
)
async def register_employee(
    user: UserCreateSchema,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    """
    Регистрация нового пользователя без авторизации с ролью "employee".
    """
    return await user_service.register(user)


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_any_user(
    user: UserFullCreateSchema,
    _: Annotated[UserModel, Depends(get_user_with_roles(Role.hr))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    """
    Регистрация нового пользователя от роли "HR".
    """
    return await user_service.register_user(user)


@router.patch("/{id}", response_model=UserSchema)
async def update_user(
    id: int,
    user: UserUpdateSchema,
    _: Annotated[UserModel, Depends(get_user_with_roles(Role.hr))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    """
    Обновление пользователя от роли "HR".
    """
    return await user_service.update(id, user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    id: int,
    _: Annotated[UserModel, Depends(get_user_with_roles(Role.hr))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """
    Деактивация пользователя от роли "HR".
    """
    await user_service.deactivate_by_id(id)


@router.patch("/{id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    id: int,
    _: Annotated[UserModel, Depends(get_user_with_roles(Role.hr))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """
    Активация пользователя от роли "HR".
    """
    await user_service.activate_by_id(id)
