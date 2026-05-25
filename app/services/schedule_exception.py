from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.models import User, ScheduleException
from app.models.user import Role
from app.schemas.schedule_exception import (
    ScheduleExceptionCreate,
    ScheduleExceptionUpdate,
)
from app.repositories import ScheduleExceptionRepository
from app.services import EmployeeService, UserService


class ScheduleExceptionService:
    def __init__(
        self,
        schedule_exception_repostitory: ScheduleExceptionRepository,
        employee_service: EmployeeService,
        user_service: UserService,
    ) -> None:
        self.schedule_exception_repostitory = schedule_exception_repostitory
        self.employee_service = employee_service
        self.user_service = user_service

    async def get_all(self, current_user: User) -> list[ScheduleException]:
        if current_user.role == Role.manager:
            return await self.schedule_exception_repostitory.get_all_by_manager_id(id)

        return self.schedule_exception_repostitory.get_all()

    async def get_all_by_user(self, current_user: User) -> list[ScheduleException]:
        db_schedule_exceptions = (
            await self.schedule_exception_repostitory.get_all_by_user_id(
                current_user.id
            )
        )

        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_by_id()

        return await db_schedule_exceptions

    async def get_by_id(self, id: int, current_user: User) -> ScheduleException:
        db_schedule_exception = await self.schedule_exception_repostitory.get_by_id(id)

        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_by_id()

        return db_schedule_exception

    async def create(
        self, shedule_exception: ScheduleExceptionCreate, current_user: User
    ) -> ScheduleException:
        pass

    async def update(
        self, id: int, shedule_exception: ScheduleExceptionUpdate, current_user: User
    ) -> ScheduleException:
        pass
