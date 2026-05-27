from sqlalchemy.exc import IntegrityError
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
)
from app.models import User, Event
from app.models.user import Role
from app.schemas.event import EventCreate, EventUpdate
from app.repositories import EventRepository, EmployeeEventRepository
from app.services import EmployeeService, TeamService


class EventService:
    def __init__(
        self,
        event_repository: EventRepository,
        employee_event_repository: EmployeeEventRepository,
        employee_service: EmployeeService,
        team_service: TeamService,
    ) -> None:
        self.event_repository = event_repository
        self.employee_event_repository = employee_event_repository
        self.employee_service = employee_service

    async def get_all(self, current_user: User) -> list[Event]:
        if current_user.role == Role.manager:
            return await self.event_repository.get_all_by_manager_id(current_user.id)
        if current_user.role == Role.employee:
            return await self.event_repository.get_all_by_user_id(current_user.id)
        return await self.event_repository.get_all()

    async def get_all_by_user_id(self, user_id: int) -> list[Event]:
        return await self.event_repository.get_all_by_user_id(user_id)

    async def get_all_by_user(self, current_user: User) -> list[Event]:
        return await self.get_all_by_user_id(current_user.id)

    async def get_by_id(self, id: int, current_user: User) -> Event:
        db_event = await self.event_repository.get_by_id(id)
        if db_event is None:
            raise NotFoundException(f"Событие с ID {id} не найдено или неактивно")

        if current_user.role in (Role.manager, Role.employee):
            await self.employee_service.get_all_by_event_id(id, current_user)

        return db_event

    async def get_employees_by_event_id(self, id: int, current_user: User) -> list:
        await self.get_by_id(id, current_user)
        return await self.employee_service.get_all_by_event_id(id, current_user)

    async def create(self, event: EventCreate, current_user: User) -> Event:
        try:
            return await self.event_repository.create(**event.model_dump())
        except IntegrityError:
            raise ConflictException("Событие с такими данными уже существует")

    async def update(self, id: int, event: EventUpdate, current_user: User) -> Event:
        db_event = await self.get_by_id(id, current_user)
        return await self.event_repository.update(db_event, **event.model_dump())

    async def deactivate(self, id: int, current_user: User) -> None:
        db_event = await self.get_by_id(id, current_user)
        await self.event_repository.deactivate(db_event)

    async def activate(self, id: int, current_user: User) -> None:
        db_event = await self.event_repository.get_inactive_by_id(id)
        if db_event is None:
            raise NotFoundException(f"Событие с ID {id} не найдено или активно")
        await self.event_repository.activate(db_event)

    async def add_employee(
        self, event_id: int, employee_id: int, current_user: User
    ) -> None:
        await self.get_by_id(event_id, current_user)
        await self.employee_service.get_by_id(employee_id, current_user)

        if await self.employee_event_repository.exists(event_id, employee_id):
            raise ConflictException(
                f"Сотрудник с ID {employee_id} уже добавлен в событие с ID {event_id}"
            )

        await self.employee_event_repository.create(employee_id, event_id)

    async def remove_employee(
        self, event_id: int, employee_id: int, current_user: User
    ) -> None:
        await self.get_by_id(event_id, current_user)
        await self.employee_service.get_by_id(employee_id, current_user)

        await self.employee_event_repository.delete(employee_id, event_id)
