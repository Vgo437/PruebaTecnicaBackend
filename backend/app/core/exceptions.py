from fastapi import Request
from app.core.logging import logger
from sqlalchemy.exc import DBAPIError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy.exc import DBAPIError

async def database_exception_handler(request: Request, exc: DBAPIError):
    """Maneja errores de conexion/comunicacion con la base de datos."""
    logger.error(
        "Error de base de datos",
        extra={
            "method": request.method,
            "endpoint": request.url.path,
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
        },
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Servicio temporalmente no disponible, intente más tarde"},
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja las HTTPException lanzadas explicitamente (404, 409, 422, etc.)."""
    logger.warning(
        "Excepcion HTTP controlada",
        extra={
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Maneja cualquier excepcion NO prevista, evitando exponer detalles tecnicos al cliente."""
    logger.error(
        "Excepcion no manejada",
        extra={
            "method": request.method,
            "endpoint": request.url.path,
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


