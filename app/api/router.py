from fastapi import APIRouter

from app.api.endpoints import auth_router, user_router, team_router, employee_router


api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(team_router)
api_router.include_router(employee_router)
