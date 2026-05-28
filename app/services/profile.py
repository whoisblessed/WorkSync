from app.core.exceptions import NotFoundException, ForbiddenException
from app.models import User, Employee
from app.schemas.profile import Profile
from app.services import (
    UserService,
    EmployeeService,
    TeamService,
    ScheduleService,
    ScheduleExceptionService,
    EventService,
)


class ProfileService:
    def __init__(
        self,
        user_service: UserService,
        employee_service: EmployeeService,
        team_service: TeamService,
        schedule_service: ScheduleService,
        schedule_exception_service: ScheduleExceptionService,
        event_service: EventService,
    ) -> None:
        self.user_service = user_service
        self.employee_service = employee_service
        self.team_service = team_service
        self.schedule_service = schedule_service
        self.schedule_exception_service = schedule_exception_service
        self.event_service = event_service

    async def get_all(self, current_user: User) -> list[Profile]:
        employees = await self.employee_service.get_all(current_user)

        profiles = []
        for employee in employees:
            user = await self.user_service.get_by_id(employee.user_id)
            profiles.append(await self._build_profile(user, employee, current_user))

        return profiles

    async def get_by_id(self, user_id: int, current_user: User) -> Profile:
        employee = await self.employee_service.get_by_user_id(user_id)
        await self.employee_service.get_by_id(employee.id, current_user)

        user = await self.user_service.get_by_id(user_id)
        return await self._build_profile(user, employee, current_user)

    async def get_profile(self, current_user: User) -> Profile:
        return await self.get_by_id(current_user.id, current_user)

    async def _build_profile(
        self, user: User, employee: Employee, current_user: User
    ) -> Profile:
        team = None
        schedule = None

        if employee.team_id is not None:
            team = await self.team_service.get_by_id(employee.team_id, current_user)


        try:
            schedule = await self.schedule_service.get_by_user_id(employee.user_id)
        except NotFoundException:
            pass

        schedule_exceptions = await self.schedule_exception_service.get_all_by_user_id(
            employee.user_id
        )
        events = await self.event_service.get_all_by_user_id(employee.user_id)

        return Profile(
            user=user,
            employee=employee,
            team=team,
            schedule=schedule,
            schedule_exceptions=schedule_exceptions,
            events=events,
        )
