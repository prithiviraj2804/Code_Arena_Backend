from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from typing import AsyncGenerator
from sqlalchemy_utils import create_database, database_exists


create_db_url = settings.postgresql_database_master_url.replace("+asyncpg", "")

def create_engine(url, **kwargs):
    """Create an asynchronous SQLAlchemy engine."""
    return create_async_engine(url, echo=False, **kwargs)

def create_database_if_not_exists():
    if not database_exists(create_db_url):
        create_database(create_db_url)
        return True
    return False


# ✅ Add `expire_on_commit=False` to prevent session expiration
master_db_engine = create_engine(settings.postgresql_database_master_url)
slave_db_engine = create_engine(
    settings.postgresql_database_slave_url,
    pool_size=10, max_overflow=20, pool_recycle=3600, pool_timeout=30, pool_pre_ping=True
)

# ✅ Add `expire_on_commit=False`
async_master_session = async_sessionmaker(
    bind=master_db_engine, autocommit=False, autoflush=False, expire_on_commit=False
)
async_slave_session = async_sessionmaker(
    bind=slave_db_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


# ✅ Provide correct session management
async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a write database session.
    """
    async with async_master_session() as session:
        try:
            yield session  # ✅ Correct session management
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a read database session.
    """
    async with async_slave_session() as session:
        try:
            yield session  # ✅ Correct session management
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
