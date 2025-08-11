from settings import settings
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    url=settings.postgres.URL,
    pool_size=5,
    max_overflow=10
)

async_db_session = async_sessionmaker(engine)


class Base(DeclarativeBase):
    pass

