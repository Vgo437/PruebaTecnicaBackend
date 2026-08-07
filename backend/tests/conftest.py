import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# Usa EXCLUSIVAMENTE la base de datos de test, nunca la real
engine_test = create_async_engine(settings.database_url_test)
SessionTest = async_sessionmaker(engine_test, expire_on_commit=False)


async def get_db_test():
    async with SessionTest() as session:
        yield session


app.dependency_overrides[get_db] = get_db_test


@pytest.fixture(scope="session", autouse=True)
async def crear_tablas():
    """Crea las tablas en la BD de test al iniciar la sesion de tests."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
async def limpiar_base_de_datos():
    """Limpia la tabla de solicitudes antes de cada test."""
    async with engine_test.begin() as conn:
        await conn.execute(Base.metadata.tables["solicitudes"].delete())
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac