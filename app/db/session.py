from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Выдает асинхронное подключение к БД
    """
    #мяу

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
