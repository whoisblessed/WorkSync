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
    """
    Карта доступности сотрудников за указанный месяц.

    - **month**: номер месяца (1–12).
    - Год определяется автоматически как текущий год в таймзоне запрашивающего.
    - Таймзона берётся из графика текущего HR/менеджера.
    - HR видит всех сотрудников, менеджер — только из своих команд.
    - Слот = 1 час (8:00–20:00 включительно).
    - Сотрудник недоступен, если: нет графика, не рабочий день,
      час за пределами рабочего времени, есть исключение (отпуск и т.д.)
      или событие (задача/встреча) в этот час.
    """
    return await availability_service.get_availability_map(month, current_user)
