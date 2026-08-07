import time
import uuid
from app.core.logging import logger
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Registra cada request con su id de correlacion, metodo, endpoint, status y duracion."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        inicio = time.time()

        response = await call_next(request)

        duracion_ms = round((time.time() - inicio) * 1000, 2)

        logger.info(
            "Request procesado",
            extra={
                "request_id": request_id,
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duracion_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response