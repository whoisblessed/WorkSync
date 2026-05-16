from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    time_zone: Mapped[str] = mapped_column(default="Europe/Moscow")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), unique=True)

    user: Mapped["User"] = relationship(back_populates="employee")
    team: Mapped["Team"] = relationship(back_populates="employees")
    schedule: Mapped["Schedule"] = relationship(back_populates="employee", cascade="all, delete-orphan")
    schedule_exceptions: Mapped[list["ScheduleException"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship(secondary="employee_events", back_populates="employees")