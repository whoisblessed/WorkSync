from app.core.exceptions import ForbiddenException, NotFoundException
from app.models import User, Event, Employee
from app.models.user import Role
from app.repositories.events import EventRepository
from app.services.employee import EmployeeService
from app.schemas.events import EventCreate, EventUpdate


class EventService:
    def __init__(
        self,
        event_repository: EventRepository,
        employee_service: EmployeeService,
    ) -> None:
        self.event_repository = event_repository
        self.employee_service = employee_service



    async def _resolve_employees(
        self, employee_ids: list[int], current_user: User
    ) -> list[Employee]:
        """
        Возвращает список Employee по переданным ID.
        Для manager — проверяет, что каждый сотрудник из его команды.
        Для hr   — разрешает любых сотрудников.
        """
        employees: list[Employee] = []
        for emp_id in employee_ids:
            # get_by_id уже содержит проверку принадлежности команде для manager
            db_employee = await self.employee_service.get_by_id(emp_id, current_user)
            employees.append(db_employee)
        return employees

    async def _get_event_or_403(self, event_id: int, current_user: User) -> Event:
        """
        Получает событие и проверяет доступ:
          - hr   — доступно любое событие
          - manager — только если хотя бы один участник из его команды
          - employee — только если он сам участник
        """
        db_event = await self.event_repository.get_by_id(event_id)
        if db_event is None:
            raise NotFoundException(f"Событие с id {event_id} не найдено или неактивно")

        if current_user.role == Role.hr:
            return db_event

        participant_ids = {emp.id for emp in db_event.employees}

        if current_user.role == Role.manager:
            # Проверяем, что хотя бы один участник — из команды менеджера
            team_employee_ids = {
                emp.id
                for emp in await self.employee_service.employee_repository.get_all_by_manager_id(
                    current_user.id
                )
            }
            if not participant_ids & team_employee_ids:
                raise ForbiddenException(
                    "У вас нет доступа к этому событию: ни один участник не входит в вашу команду"
                )
            return db_event

        # employee
        my_employee = await self.employee_service.employee_repository.get_by_user_id(
            current_user.id
        )
        if my_employee is None or my_employee.id not in participant_ids:
            raise ForbiddenException("Вы не являетесь участником этого события")

        return db_event


    async def get_all(self, current_user: User) -> list[Event]:
        if current_user.role == Role.hr:
            return await self.event_repository.get_all()

        if current_user.role == Role.manager:
            return await self.event_repository.get_all_by_manager_id(current_user.id)

        # employee — только свои
        my_employee = await self.employee_service.employee_repository.get_by_user_id(
            current_user.id
        )
        if my_employee is None:
            return []
        return await self.event_repository.get_all_by_employee_id(my_employee.id)

    async def get_by_id(self, event_id: int, current_user: User) -> Event:
        return await self._get_event_or_403(event_id, current_user)


    async def create(self, data: EventCreate, current_user: User) -> Event:
        employees = await self._resolve_employees(data.employee_ids, current_user)

        return await self.event_repository.create_with_employees(
            employees=employees,
            type=data.type,
            title=data.title,
            description=data.description,
            start_at=data.start_at,
            end_at=data.end_at,
        )

    async def update(
        self, event_id: int, data: EventUpdate, current_user: User
    ) -> Event:
        db_event = await self._get_event_or_403(event_id, current_user)

        return await self.event_repository.update(
            db_event,
            type=data.type,
            title=data.title,
            description=data.description,
            start_at=data.start_at,
            end_at=data.end_at,
        )

    async def deactivate(self, event_id: int, current_user: User) -> None:
        db_event = await self._get_event_or_403(event_id, current_user)
        await self.event_repository.deactivate(db_event)

    async def activate(self, event_id: int, current_user: User) -> None:
        db_event = await self.event_repository.get_inactive_by_id(event_id)
        if db_event is None:
            raise NotFoundException(
                f"Неактивное событие с id {event_id} не найдено"
            )
        # Для activate тоже проверяем доступ через участников (загружены при get_inactive_by_id)
        if current_user.role == Role.manager:
            participant_ids = {emp.id for emp in db_event.employees}
            team_employee_ids = {
                emp.id
                for emp in await self.employee_service.employee_repository.get_all_by_manager_id(
                    current_user.id
                )
            }
            if not participant_ids & team_employee_ids:
                raise ForbiddenException(
                    "У вас нет доступа к этому событию"
                )
        await self.event_repository.activate(db_event)