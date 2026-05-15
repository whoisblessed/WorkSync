from enum import Enum
from datetime import time

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WorkFormat(Enum):
    office: str = "office"
    remote: str = "remote"
    hybrid: str = "hybrid"


class Shelude(Base):
    __tablename__ = "sheludes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    work_format: Mapped[WorkFormat] = mapped_column(default=WorkFormat.office)
    shift_start_date: Mapped
    