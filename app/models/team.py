from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


if TYPE_CHECKING:
    from app.models import Employee, User


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)

    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    employees: Mapped[list[Employee]] = relationship(back_populates="team")
    manager: Mapped[User] = relationship(back_populates="teams")
