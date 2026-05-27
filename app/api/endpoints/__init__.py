from .auth import router as auth_router
from .user import router as user_router
from .team import router as team_router
from .employee import router as employee_router
from .schedule import router as schedule_router
from .schedule_exception import router as schedule_exception_router

__all__ = [
    "auth_router",
    "user_router",
    "team_router",
    "employee_router",
    "schedule_router",
    "schedule_exception_router"
]
