from .auth import router as auth_router
from .user import router as user_router
from .team import router as team_router
from .employee import router as employee_router
from .schedule import router as schedule_router
from .schedule_exception import router as schedule_exception_router
from .event import router as event_router
from .profile import router as profile_router
from .availability_map import router as availability_map_router
from .ai_assistant import router as ai_assistant_router

__all__ = [
    "auth_router",
    "user_router",
    "team_router",
    "employee_router",
    "schedule_router",
    "schedule_exception_router",
    "event_router",
    "profile_router",
    "availability_map_router",
    "ai_assistant_router",
]
