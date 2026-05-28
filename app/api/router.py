from fastapi import APIRouter

from app.api.endpoints import (
    auth_router,
    user_router,
    team_router,
    employee_router,
    schedule_router,
    schedule_exception_router,
    event_router,
    profile_router,
    availability_map_router,
)


api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(team_router)
api_router.include_router(employee_router)
api_router.include_router(schedule_router)
api_router.include_router(schedule_exception_router)
api_router.include_router(event_router)
api_router.include_router(profile_router)
api_router.include_router(availability_map_router)
