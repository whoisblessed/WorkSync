from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[ModelType]:
        result = await self.session.scalars(
            select(self.model).where(self.model.is_active)
        )
        return result.all()

    async def get_all_inactive(self) -> list[ModelType]:
        result = await self.session.scalars(
            select(self.model).where(~self.model.is_active)
        )
        return result.all()

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        return await self.session.scalar(
            select(self.model).where(self.model.id == obj_id, self.model.is_active)
        )

    async def get_inactive_by_id(self, obj_id: int) -> ModelType | None:
        return await self.session.scalar(
            select(self.model).where(self.model.id == obj_id, ~self.model.is_active)
        )

    async def create(self, **kwargs: Any) -> ModelType:
        obj = self.model(**kwargs)

        self.session.add(obj)

        await self.session.flush()
        await self.session.refresh(obj)

        return obj

    async def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        for key, value in kwargs.items():
            setattr(obj, key, value)

        await self.session.flush()
        await self.session.refresh(obj)

        return obj

    async def deactivate(self, obj: ModelType) -> None:
        obj.is_active = False
        await self.session.flush()

    async def activate(self, obj: ModelType) -> None:
        obj.is_active = True
        await self.session.flush()
