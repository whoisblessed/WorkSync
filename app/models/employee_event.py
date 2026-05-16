from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EmployeeEvent(Base):
    __tablename__ = "employee_events"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    