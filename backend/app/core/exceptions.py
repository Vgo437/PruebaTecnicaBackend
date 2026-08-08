from fastapi import Request
from app.core.logging import logger
from sqlalchemy.exc import DBAPIError
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.domain_exceptions import (
    SolicitudNoEncontrada,
    IdentificadorDuplicado,
    TransicionInvalida,
)


async def domain_exception_handler(request: Request, exc: Exception):
    """Traduce excepciones de dominio (negocio) a respuestas HTTP apropiadas."""
    if isinstance(exc, SolicitudNoEncontrada):
        status_code, detail = 404, "Solicitud no encontrada"
    elif isinstance(exc, IdentificadorDuplicado):
        status_code, detail = 409, "El identificador externo ya existe"
    elif isinstance(exc, TransicionInvalida):
        status_code, detail = 422, str(exc)
    else:
        status_code, detail = 500, "Error interno del servidor"

    logger.warning(
        "Excepcion de dominio",
        extra={
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": status_code,
            "detail": detail,
        },
    )
    return JSONResponse(status_code=status_code, content={"detail": detail})



async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Transforma los errores de validacion de Pydantic en mensajes legibles para el cliente."""
    errores_legibles = []

    for error in exc.errors():
        campo = error["loc"][-1]  # el nombre del campo que fallo
        tipo_error = error["type"]

        if tipo_error == "missing":
            mensaje = f"El campo '{campo}' es obligatorio"
        elif tipo_error in ("string_type", "int_type", "float_type", "bool_type"):
            mensaje = f"El campo '{campo}' tiene un formato incorrecto"
        elif tipo_error == "enum":
            mensaje = f"El campo '{campo}' tiene un valor no permitido"
        elif tipo_error == "value_error":
            mensaje = f"El campo '{campo}' no es valido: {error['msg']}"
        else:
            mensaje = f"El campo '{campo}' tiene un formato incorrecto"

        errores_legibles.append(mensaje)

    logger.warning(
        "Error de validacion de datos",
        extra={
            "method": request.method,
            "endpoint": request.url.path,
            "errores": errores_legibles,
        },
    )

    return JSONResponse(
        status_code=422,
        content={"detail": errores_legibles},
    )

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


