from __future__ import annotations
from typing import TYPE_CHECKING

from enum import Enum
from datetime import date

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


if TYPE_CHECKING:
    from app.models import Employee


class ScheduleExceptionType(Enum):
    vacation: str = "vacation"
    sick_leave: str = "sick_leave"
    personal: str = "personal"
    business_trip: str = "business_trip"


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ScheduleExceptionType] = mapped_column()
    description: Mapped[str | None] = mapped_column(String(500))
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    employee: Mapped[Employee] = relationship(back_populates="schedule_exceptions")
