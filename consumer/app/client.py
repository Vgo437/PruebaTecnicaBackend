import httpx
import uuid
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)


def es_error_temporal(exc: BaseException) -> bool:
    """Determina si un error amerita reintento: timeouts, errores de conexión, o 5xx."""
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


class ApiClient:
    """Cliente HTTP para consumir la API de solicitudes, con reintentos automaticos."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(es_error_temporal),
        reraise=True,
    )
    async def crear_solicitud(self, client: httpx.AsyncClient, payload: dict, request_id: str) -> dict:
        response = await client.post(
            f"{self.base_url}/solicitudes",
            json=payload,
            timeout=self.timeout,
            headers={"X-Request-ID": request_id},
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(es_error_temporal),
        reraise=True,
    )
    async def obtener_solicitud(self, client: httpx.AsyncClient, id: int, request_id: str) -> dict:
        response = await client.get(
            f"{self.base_url}/solicitudes/{id}",
            timeout=self.timeout,
            headers={"X-Request-ID": request_id},
        )
        response.raise_for_status()
        return response.json()