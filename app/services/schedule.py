from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
)
from app.models import User, Schedule
from app.models.user import Role
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.repositories import ScheduleRepository
from app.services import EmployeeService


class ScheduleService:
    def __init__(
        self,
        schedule_repository: ScheduleRepository,
        employee_service: EmployeeService,
    ) -> None:
        self.schedule_repository = schedule_repository
        self.employee_service = employee_service

    # Получние

    async def get_all(self, current_user: User) -> list[Schedule]:
        if current_user.role == Role.manager:
            return await self.schedule_repository.get_all_by_manager_id(current_user.id)

        return await self.schedule_repository.get_all()

    async def get_by_user_id(self, user_id: int) -> Schedule:
        db_schedule = await self.schedule_repository.get_by_user_id(user_id)
        if db_schedule is None:
            raise NotFoundException(
                f"График пользователя с id {user_id} не найден или неактивен"
            )
        return db_schedule

    async def get_by_user(self, current_user: User) -> Schedule:
        return await self.get_by_user_id(current_user.id)

    async def get_by_id(self, id: int, current_user: User) -> Schedule:
        db_schedule = await self.schedule_repository.get_by_id(id)

        if db_schedule is None:
            raise NotFoundException(f"График с ID {id} не найден или неактивен")

        # Проверка принадлежности графика сотруднику из команды руководителя
        # или личных данных сотруднику
        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_by_id(db_schedule.employee_id, current_user)

        return db_schedule

    async def get_by_employee_id(self, id: int, current_user: User) -> Schedule:
        db_schedule = await self.schedule_repository.get_by_employee_id(id)

        if db_schedule is None:
            raise NotFoundException(
                f"График сотрудника с ID {id} не найден или неактивен"
            )

        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_by_id(id, current_user)

        return db_schedule

    # Изменение

    async def create(self, schedule: ScheduleCreate, current_user: User) -> Schedule:
        await self.employee_service.get_by_id(
            schedule.employee_id, current_user
        )  # Проверка существования данных сотрудника + принадлежности сотрудника команде руководителя

        try:
            return await self.schedule_repository.create(**schedule.model_dump())
        except IntegrityError:
            raise ConflictException(
                f"График для сотрудника с ID {schedule.employee_id} уже существует"
            )

    async def update(
        self, id: int, schedule: ScheduleUpdate, current_user: User
    ) -> Schedule:
        db_schedule = await self.get_by_id(
            id, current_user
        )  # Проверка существования схемы и принадлежности его к руководителю или сотруднкиу

        return await self.schedule_repository.update(
            db_schedule, **schedule.model_dump()
        )
