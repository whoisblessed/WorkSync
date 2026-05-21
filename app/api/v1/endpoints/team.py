from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, user_require_roles, get_user_service
from app.models import User as UserModel
from app.models.user import Role
from app.shemas.user import (
    User as UserSchema,
    UserCreate as UserCreateSchema,
    UserFullCreate as UserFullCreateSchema,
    UserUpdate as UserUpdateSchema,
)
from app.services import UserService