from enum import Enum
from datetime import date

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SheludeExceptionType(Enum):
    vacation: str = "vacation"
    sick_leave: str = "sick_leave"
    personal: str = "personal"
    business_trip: str = "business_trip"
    

class SheludeException(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[SheludeExceptionType] = mapped_column()
    description: Mapped[str | None] = mapped_column(String(500))
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column