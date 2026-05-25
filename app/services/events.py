from app.core.exceptions import BadRequestException, NotFoundException
from app.models import Event as EventModel
from app.repositories import EventRepository, EmployeeRepository
from app.schemas.events import EventCreate, EventUpdate, Event as EventSchema


class EventService:

    def __init__(
            self,
            event_repository: EventRepository,
            employee_repository: EmployeeRepository,
    ):
        self.event_repository = event_repository
        self.employee_repository = employee_repository

    """Получить все активные события"""
    async def get_all(self) -> list[EventSchema]:
        events = await self.event_repository.get_all()
        return [self._to_schema(event) for event in events]

    """Получить событие по ID"""
    async def get_by_id(self, event_id: int) -> EventSchema:
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise NotFoundException(f"Событие с ID {event_id} не найдено")
        return self._to_schema(event)

    """Получить все события сотрудника"""
    async def get_by_employee_id(self, employee_id: int) -> list[EventSchema]:
        # Проверяем существование сотрудника
        employee = await self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise NotFoundException(f"Сотрудник с ID {employee_id} не найден")

        events = await self.event_repository.get_by_employee_id(employee_id)
        return [self._to_schema(event) for event in events]

    """Создать новое событие"""
    async def create(self, data: EventCreate) -> EventSchema:
        """Создать новое событие"""
        # Валидация времени
        if data.end_at <= data.start_at:
            raise BadRequestException(
                "Время окончания должно быть позже времени начала"
            )

        # Проверка существования сотрудников
        all_employees = await self.employee_repository.get_all()
        existing_ids = {emp.id for emp in all_employees}

        if not set(data.employee_ids).issubset(existing_ids):
            missing_ids = set(data.employee_ids) - existing_ids
            raise NotFoundException(
                f"Сотрудники с ID {missing_ids} не найдены"
            )

        # Создание события
        event_data = data.dict(exclude={'employee_ids'})
        event = await self.event_repository.create(event_data)

        # Добавление участников
        await self.event_repository.update_employees(event.id, data.employee_ids)

        # Получение обновленного события
        updated_event = await self.event_repository.get_by_id(event.id)
        return self._to_schema(updated_event)

    async def update(self, event_id: int, data: EventUpdate) -> EventSchema:
        """Обновить событие"""
        # Проверка существования
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise NotFoundException(f"Событие с ID {event_id} не найдено")

        # Валидация времени
        final_start = data.start_at if data.start_at is not None else event.start_at
        final_end = data.end_at if data.end_at is not None else event.end_at

        if final_end <= final_start:
            raise BadRequestException(
                "Время окончания должно быть позже времени начала"
            )

        # Обновление основных полей
        update_data = data.dict(exclude_unset=True, exclude={'employee_ids'})
        event = await self.event_repository.update(event_id, update_data)

        # Обновление участников
        if data.employee_ids is not None:
            all_employees = await self.employee_repository.get_all()
            existing_ids = {emp.id for emp in all_employees}

            if not set(data.employee_ids).issubset(existing_ids):
                missing_ids = set(data.employee_ids) - existing_ids
                raise NotFoundException(
                    f"Сотрудники с ID {missing_ids} не найдены"
                )

            await self.event_repository.update_employees(
                event_id, data.employee_ids
            )

        # Получение обновленного события
        updated_event = await self.event_repository.get_by_id(event_id)
        return self._to_schema(updated_event)

    async def delete(self, event_id: int) -> None:
        """Деактивировать событие (soft delete)"""
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise NotFoundException(f"Событие с ID {event_id} не найдено")

        await self.event_repository.deactivate(event_id)

    def _to_schema(self, event: EventModel) -> EventSchema:
        """Конвертировать SQLAlchemy модель в Pydantic схему"""
        employee_ids = [emp.id for emp in event.employees]
        event_schema = EventSchema.model_validate(event)
        event_schema.employee_ids = employee_ids
        return event_schema
