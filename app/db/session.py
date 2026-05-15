from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Выдает асинхронное подключение к БД
    """

    async with async_session_maker() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
