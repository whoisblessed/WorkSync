from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EmployeeEvent(Base):
    __tablename__ = "employee_events"

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"), primary_key=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
