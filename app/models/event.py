from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Event(Base):
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(500))
    start_at: Mapped[datetime] = mapped_column()
    end_at: Mapped[datetime] = mapped_column()

    employees: Mapped[list["Employee"]] = relationship(secondary="employee_events", back_populates="events")