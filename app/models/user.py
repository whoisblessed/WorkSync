from __future__ import annotations
from typing import TYPE_CHECKING

from enum import Enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


if TYPE_CHECKING:
    from app.models import Employee, Team


class Role(Enum):
    employee: str = "employee"
    manager: str = "manager"
    hr: str = "hr"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    employee: Mapped[Employee] = relationship(back_populates="user")
    teams: Mapped[list[Team]] = relationship(back_populates="manager")
