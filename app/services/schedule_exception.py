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
            return await self.schedule_exception_repostitory.get_all_by_manager_id(
                current_user.id
            )

        if current_user.role == Role.employee:
            return await self.schedule_exception_repostitory.get_all_by_user_id(
                current_user.id
            )

        return await self.schedule_exception_repostitory.get_all()

    async def get_by_id(self, id: int, current_user: User) -> ScheduleException:
        db_schedule_exception = await self.schedule_exception_repostitory.get_by_id(id)

        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_by_id(
                db_schedule_exception.employee_id, current_user
            )

        return db_schedule_exception

    async def create(
        self, shedule_exception: ScheduleExceptionCreate, current_user: User
    ) -> ScheduleException:
        db_employee = await self.employee_service.get_by_id(
            shedule_exception.employee_id, current_user
        )
        db_user = await self.user_service.get_by_id(db_employee.user_id)

        if db_user.role != Role.employee:
            raise BadRequestException(
                f"Сотрудник с id {shedule_exception.employee_id} не имеет соответсвующей роли"
            )

        return await self.schedule_exception_repostitory.create(
            **shedule_exception.model_dump()
        )

    async def update(
        self, id: int, shedule_exception: ScheduleExceptionUpdate, current_user: User
    ) -> ScheduleException:
        db_schedule_exception = await self.get_by_id(id, current_user)

        return await self.schedule_exception_repostitory.update(
            db_schedule_exception, **shedule_exception.model_dump()
        )
