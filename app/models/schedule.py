from enum import Enum
from datetime import date, datetime, time

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WorkFormat(Enum):
    office: str = "office"
    remote: str = "remote"
    hybrid: str = "hybrid"


class Schedule(Base):
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    work_format: Mapped[WorkFormat] = mapped_column(default=WorkFormat.office)
    start_at: Mapped[time] = mapped_column(default=time(9, 0))
    end_at: Mapped[time] = mapped_column(default=time(18, 0))
    shift_start_date: Mapped[date] = mapped_column()
    shift_work_days: Mapped[int] = mapped_column(default=5)
    shift_rest_days: Mapped[int] = mapped_column(default=2)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    employee: Mapped["Employee"] = relationship(back_populates="schedule")