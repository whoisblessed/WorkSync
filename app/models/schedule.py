from __future__ import annotations
from typing import TYPE_CHECKING


from enum import Enum
from datetime import date, datetime, time

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models import Employee


class WorkFormat(Enum):
    office: str = "office"
    remote: str = "remote"
    hybrid: str = "hybrid"


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    time_zone: Mapped[str] = mapped_column(default="Europe/Moscow")
    work_format: Mapped[WorkFormat] = mapped_column(default=WorkFormat.office)
    start_at: Mapped[time] = mapped_column(default=time(9, 0))
    end_at: Mapped[time] = mapped_column(default=time(18, 0))
    shift_start_date: Mapped[date] = mapped_column()
    shift_work_days: Mapped[int] = mapped_column(default=5)
    shift_rest_days: Mapped[int] = mapped_column(default=2)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), unique=True)

    employee: Mapped[Employee] = relationship(back_populates="schedule")
