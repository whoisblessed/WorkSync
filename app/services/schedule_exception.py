from app.core.exceptions import NotFoundException
from app.models import User, ScheduleException
from app.models.user import Role
from app.schemas.schedule_exception import (
    ScheduleExceptionCreate,
    ScheduleExceptionUpdate,
)
from app.repositories import ScheduleExceptionRepository
from app.services import EmployeeService


class ScheduleExceptionService:
    def __init__(
        self,
        schedule_exception_repository: ScheduleExceptionRepository,
        employee_service: EmployeeService,
    ) -> None:
        self.schedule_exception_repository = schedule_exception_repository
        self.employee_service = employee_service

    async def get_all(self, current_user: User) -> list[ScheduleException]:
        if current_user.role == Role.manager:
            return await self.schedule_exception_repository.get_all_by_manager_id(
                current_user.id
            )

        if current_user.role == Role.employee:
            return await self.schedule_exception_repository.get_all_by_user_id(
                current_user.id
            )

        return await self.schedule_exception_repository.get_all()

    async def get_all_by_user_id(self, user_id: int) -> list[ScheduleException]:
        return await self.schedule_exception_repository.get_all_by_user_id(user_id)

    async def get_all_by_user(self, current_user: User) -> list[ScheduleException]:
        return await self.get_all_by_user_id(current_user.id)

    async def get_by_id(self, id: int, current_user: User) -> ScheduleException:
        db_schedule_exception = await self.schedule_exception_repository.get_by_id(id)

        if db_schedule_exception is None:
            raise NotFoundException(f"Исключение с ID {id} не найдено или неактивно")

        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_by_id(
                db_schedule_exception.employee_id, current_user
            )

        return db_schedule_exception

    async def create(
        self, shedule_exception: ScheduleExceptionCreate, current_user: User
    ) -> ScheduleException:
        await self.employee_service.get_by_id(
            shedule_exception.employee_id, current_user
        )

        return await self.schedule_exception_repository.create(
            **shedule_exception.model_dump()
        )

    async def update(
        self, id: int, shedule_exception: ScheduleExceptionUpdate, current_user: User
    ) -> ScheduleException:
        db_schedule_exception = await self.get_by_id(id, current_user)

        return await self.schedule_exception_repository.update(
            db_schedule_exception, **shedule_exception.model_dump()
        )
