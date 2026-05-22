from __future__ import annotations
from typing import TYPE_CHECKING


from enum import Enum
from datetime import datetime, time

from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

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
    work_days: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), default=[1, 2, 3, 4, 5]
    )
    time_zone: Mapped[str] = mapped_column(default="Europe/Moscow")
    work_format: Mapped[WorkFormat] = mapped_column(default=WorkFormat.office)
    start_at: Mapped[time] = mapped_column(default=time(9, 0))
    end_at: Mapped[time] = mapped_column(default=time(18, 0))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), unique=True)

    employee: Mapped[Employee] = relationship(back_populates="schedule")
