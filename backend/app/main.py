from sqlalchemy import text
from app.db.session import get_db
from fastapi import FastAPI, Depends
from sqlalchemy.exc import DBAPIError
from app.api.solicitudes import router
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.middleware import LoggingMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    unhandled_exception_handler,
)

app = FastAPI(title="API de Solicitudes Institucionales para prueba tecnica", version="1.0.0")


app.include_router(router)
app.add_middleware(LoggingMiddleware)
app.add_exception_handler(OSError, database_exception_handler)
app.add_exception_handler(DBAPIError, database_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
async def health():
    """Consulta el estado de la API"""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Consulta que la conexion a la bd esta funcionando"""
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}