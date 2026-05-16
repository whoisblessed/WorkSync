from pydantic import BaseModel, ConfigDict


class TeamShortResponse(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ScheduleShortResponse(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ScheduleExceptionShortResponse(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EventShortResponse(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    time_zone: str = "Europe/Moscow"


class EmployeeCreate(EmployeeBase):
    user_id: int
    team_id: int
    schedule_id: int


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    time_zone: str | None = None
    team_id: int | None = None
    schedule_id: int | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    team_id: int
    schedule_id: int
    team: TeamShortResponse
    schedule: ScheduleShortResponse | None = None
    schedule_exceptions: list[ScheduleExceptionShortResponse]
    events: list[EventShortResponse]

    model_config = ConfigDict(from_attributes=True)