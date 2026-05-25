from .auth import router as auth_router
from .user import router as user_router
from .team import router as team_router
from .employee import router as employee_router

__all__ = ["auth_router", "user_router", "team_router", "employee_router"]
