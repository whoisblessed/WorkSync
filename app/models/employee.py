from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


if TYPE_CHECKING:
    from app.models import User, Team, Schedule, ScheduleException, Event


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    patronymic: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    user: Mapped[User] = relationship(back_populates="employee")
    team: Mapped[Team] = relationship(back_populates="employees")
    schedule: Mapped[Schedule] = relationship(back_populates="employee")
    schedule_exceptions: Mapped[list[ScheduleException]] = relationship(
        back_populates="employee"
    )
    events: Mapped[list[Event]] = relationship(
        secondary="employee_events", back_populates="employees"
    )
