from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.models import User, Event
from app.models.user import Role
from app.schemas.event import EventCreate, EventUpdate
from app.repositories import EventRepository, EmployeeEventRepository
from app.services import EmployeeService


class EventService:
    def __init__(
        self,
        event_repository: EventRepository,
        employee_event_repository: EmployeeEventRepository,
        employee_service: EmployeeService,
    ) -> None:
        self.event_repository = event_repository
        self.employee_event_repository = employee_event_repository
        self.employee_service = employee_service

    async def get_all(self, current_user: User) -> list[Event]:
        if current_user.role == Role.manager:
            return await self.event_repository.get_all_by_manager_id(id)

        if current_user.role == Role.employee:
            return await self.event_repository.get_all_by_user_id(id)

        return self.event_repository.get_all()

    async def get_by_user(self, current_user: User) -> list[Event]:
        return await self.event_repository.get_all_by_user_id(id)

    async def get_by_id(self, id: int, current_user: User) -> Event:
        db_event = await self.event_repository.get_by_id(id)

        if db_event is None:
            raise NotFoundException(f"Событие с ID {id} не найдено или неактивно")

        if current_user.role in (Role.manager, Role.employee):
            pass
