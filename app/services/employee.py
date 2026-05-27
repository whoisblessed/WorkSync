from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.models import User, Employee
from app.models.user import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.repositories import EmployeeRepository
from app.services import UserService, TeamService


class EmployeeService:
    def __init__(
        self,
        employee_repository: EmployeeRepository,
        user_service: UserService,
        team_service: TeamService,
    ) -> None:
        self.employee_repository = employee_repository
        self.user_service = user_service
        self.team_service = team_service

    # Получение

    async def get_all(self, current_user: User) -> list[Employee]:
        if current_user.role == Role.manager:
            return await self.employee_repository.get_all_by_manager_id(current_user.id)

        return await self.employee_repository.get_all()

    async def get_by_user_id(self, user_id: int) -> Employee:
        db_employee = await self.employee_repository.get_by_user_id(user_id)

        if db_employee is None:
            raise NotFoundException(
                f"Сотрудник пользователя с id {user_id} не найден или неактивен"
            )

        return db_employee

    async def get_by_user(self, current_user: User) -> Employee:
        return await self.get_by_user_id(current_user.id)

    async def get_by_id(self, id: int, current_user: User) -> Employee:
        db_employee = await self.employee_repository.get_by_id(id)

        if db_employee is None:
            raise NotFoundException(f"Сотрудник с id {id} не найден или неактивен")

        if current_user.role == Role.manager:
            await self.team_service.get_by_id(db_employee.team_id, current_user)

        if (
            current_user.role == Role.employee
            and current_user.id != db_employee.user_id
        ):
            raise ForbiddenException(
                f"Личные данные не принадлежат сотруднику с ID {db_employee.id}"
            )

        return db_employee

    async def get_all_by_event_id(self, id: int, current_user: User) -> list[Employee]:
        db_employees = await self.employee_repository.get_all_by_event_id(id)

        if current_user.role == Role.manager:
            manager_teams = await self.team_service.get_all(current_user)
            team_ids = {team.id for team in manager_teams}
            return [e for e in db_employees if e.team_id in team_ids]

        if current_user.role == Role.employee:
            cur_employee = await self.get_by_user(current_user)
            if not any(e.id == cur_employee.id for e in db_employees):
                raise NotFoundException(
                    f"Сотруднику с ID {cur_employee.id} не было поставлено событие с ID {id}"
                )
            return [
                employee
                for employee in db_employees
                if employee.team_id == cur_employee.team_id
            ]

        return db_employees

    # Изменение

    async def create(self, employee: EmployeeCreate, current_user: User) -> Employee:
        db_user = await self.user_service.get_by_id(
            employee.user_id
        )  # Проверка существования пользователя из схемы

        if db_user.role != Role.employee and employee.team_id is not None:
            raise BadRequestException("Руководители и HR не могут иметь команды")

        if db_user.role == Role.employee and employee.team_id is None:
            raise BadRequestException("Сотрудники обязаны иметь команду")

        if employee.team_id is not None:
            await self.team_service.get_by_id(
                employee.team_id, current_user
            )  # Проверка существования команды из схемы + принадлежности команды руководителю

        try:
            return await self.employee_repository.create(**employee.model_dump())
        except IntegrityError:
            raise ConflictException(
                f"Личные данные на пользователя с id {employee.user_id} уже существуют"
            )

    async def update(
        self, id: int, employee: EmployeeUpdate, current_user: User
    ) -> Employee:
        db_employee = await self.get_by_id(
            id, current_user
        )  # Получение сотрудника из схемы и проверка его существования
        db_user = await self.user_service.get_by_id(db_employee.user_id)

        if db_user.role != Role.employee and employee.team_id is not None:
            raise BadRequestException("Руководители и HR не могут иметь команды")

        if db_user.role == Role.employee and employee.team_id is None:
            raise BadRequestException("Сотрудники обязаны иметь команду")

        if employee.team_id is not None:
            await self.team_service.get_by_id(
                employee.team_id, current_user
            )  # Проверка существования команды из схемы + принадлежности команды руководителю

        return await self.employee_repository.update(
            db_employee, **employee.model_dump()
        )
