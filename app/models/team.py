from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Team(Base):
    __tablename__ = "teams"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(500))
    
    employees: Mapped[list["Employee"]] = relationship(back_populates="team")
