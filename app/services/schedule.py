from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.models import User, Schedule
from app.models.user import Role
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.repositories import ScheduleRepository
from app.services import UserService, EmployeeService


class ScheduleService:
    def __init__(
        self,
        schedule_repository: ScheduleRepository,
        user_service: UserService,
        employee_service: EmployeeService,
    ) -> None:
        self.schedule_repository = schedule_repository
        self.user_service = user_service
        self.employee_service = employee_service

    # Получние

    async def get_all(self, current_user: User) -> list[Schedule]:
        if current_user.role == Role.manager:
            return await self.schedule_repository.get_all_by_manager_id(current_user.id)

        return await self.schedule_repository.get_all()

    async def get_by_user(self, current_user: User) -> Schedule:
        db_schedule = await self.schedule_repository.get_by_user_id(current_user.id)

        if db_schedule is None:
            raise NotFoundException(
                f"График пользователя с id {current_user.id} не найден или неактивен"
            )

        return db_schedule

    async def get_by_id(self, id: int, current_user: User) -> Schedule:
        db_schedule = await self.schedule_repository.get_by_id(id)

        if db_schedule is None:
            raise NotFoundException(f"График с ID {id} не найден или неактивен")

        if current_user.role == Role.manager:
            await self.employee_service.get_by_id(
                db_schedule.employee_id, current_user
            )  # Проверка принадлежности графика сотруднику из команды руководителя

        return db_schedule

    async def get_by_employee_id(self, id: int, current_user: User) -> Schedule:
        db_schedule = await self.schedule_repository.get_by_employee_id(id)

        if db_schedule is None:
            raise NotFoundException(
                f"График сотрудника с ID {id} не найден или неактивен"
            )

        if current_user.role == Role.manager:
            await self.employee_service.get_by_id(id, current_user)

        return db_schedule

    # Изменение

    async def create(self, schedule: ScheduleCreate, current_user: User) -> Schedule:
        db_employee = await self.employee_service.get_by_id(
            schedule.employee_id, current_user
        )  # Проверка существования данных сотрудника + принадлежности сотрудника команде руководителя

        if current_user.role == Role.employee:
            current_employee = await self.employee_service.get_by_user(current_user)

            if current_employee.id != schedule.employee_id:
                raise ForbiddenException(
                    f"Сотрудник может создать график только для себя"
                )

        db_user = await self.user_service.get_by_id(
            db_employee.user_id
        )  # Получение пользователя для првоерки его роли
        if db_user.role != Role.employee:
            raise BadRequestException(
                f"Сотрудник с id {schedule.employee_id} не имеет соответсвующей роли"
            )

        try:
            return await self.schedule_repository.create(**schedule.model_dump())
        except IntegrityError:
            raise ConflictException(
                f"График для сотрудника с ID {schedule.employee_id} уже существует"
            )

    async def update(
        self, id: int, schedule: ScheduleUpdate, current_user: User
    ) -> Schedule:
        db_schedule = await self.get_by_id(id, current_user)  # Проверка существования схемы и принадлежности ее к руководителю
