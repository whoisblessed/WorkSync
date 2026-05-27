from pydantic import BaseModel, ConfigDict

from app.schemas.user import User
from app.schemas.employee import Employee
from app.schemas.team import Team
from app.schemas.schedule import Schedule
from app.schemas.schedule_exception import ScheduleException
from app.schemas.event import Event


class Profile(BaseModel):
    user: User
    employee: Employee | None
    team: Team | None
    schedule: Schedule | None
    schedule_exceptions: list[ScheduleException]
    events: list[Event]

    model_config = ConfigDict(from_attributes=True)
