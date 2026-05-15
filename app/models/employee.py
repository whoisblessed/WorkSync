from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Employee(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    time_zone: Mapped[str] = mapped_column(default="Europe/Moscow")

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    shelude_id: Mapped[int] = mapped_column(ForeignKey("sheludes.id"), unique=True)
