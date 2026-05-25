from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
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

    async def get_by_user(self, current_user: User) -> Employee:
        db_employee = await self.employee_repository.get_by_user_id(current_user.id)

        if db_employee is None:
            raise NotFoundException(
                f"Сотрудник пользователя с id {current_user.id} не найден или неактивен"
            )

        return db_employee

    async def get_by_id(self, id: int, current_user: User) -> Employee:
        db_employee = await self.employee_repository.get_by_id(id)

        if db_employee is None:
            raise NotFoundException(f"Сотрудник с id {id} не найден или неактивен")

        if current_user.role == Role.manager:
            await self.team_service.get_by_id(db_employee.team_id, current_user)

        return db_employee

    # Изменение

    async def create(self, employee: EmployeeCreate, current_user: User) -> Employee:
        await self.user_service.get_by_id(
            employee.user_id
        )  # Проверка существования пользователя из схемы
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
        await self.team_service.get_by_id(
            employee.team_id, current_user
        )  # Проверка существования команды из схемы + принадлежности команды руководителю
        db_employee = await self.get_by_id(
            id, current_user
        )  # Получение сотрудника из схемы и проверка его существования

        return await self.employee_repository.update(
            db_employee, **employee.model_dump()
        )
