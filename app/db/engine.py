from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings


async_engine = create_async_engine(
    settings.database.url,
    echo=settings.app.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False, autoflush=False
)
