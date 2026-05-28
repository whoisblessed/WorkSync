from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_user_with_roles, get_availability_service
from app.models import User as UserModel
from app.models.user import Role
from app.schemas.availability_map import AvailabilityResponse
from app.services.availability_map import AvailabilityMapService


router = APIRouter(prefix="/availability_map", tags=["availability_map"])


@router.get("/", response_model=AvailabilityResponse)
async def get_availability_map(
    month: Annotated[int, Query(ge=1, le=12)],
    current_user: Annotated[
        UserModel, Depends(get_user_with_roles(Role.manager, Role.hr))
    ],
    availability_service: Annotated[
        AvailabilityMapService, Depends(get_availability_service)
    ],
) -> AvailabilityResponse:
    return await availability_service.get_availability_map(month, current_user)
