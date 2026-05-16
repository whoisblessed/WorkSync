from enum import Enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Role(Enum):
    manager: str = "manager"
    hr: str = "HR"
    employee: str = "employee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column()

    employee: Mapped["Employee"] = relationship(back_populates="user")
