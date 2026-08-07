from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


engine = create_async_engine(settings.database_url, echo=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session