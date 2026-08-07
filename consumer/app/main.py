import os
import sys
import httpx
import logging
import asyncio
from app.client import ApiClient
from pythonjsonlogger import jsonlogger


logger = logging.getLogger("consumer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level", "name": "service"},
)
handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(handler)


API_URL = os.getenv("API_URL", "http://api:8000")

SOLICITUDES_DE_PRUEBA = [
    {
        "identificador_externo": "TICKET-001",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "Cliente 1",
        "correo_electronico": "cliente1@gmail.com",
        "descripcion": "Solicitud generada por el consumidor prueba 1",
        "prioridad": "alta",
    },
    {
        "identificador_externo": "TICKET-002",
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Cliente 2",
        "correo_electronico": "cliente2@gmail.com",
        "descripcion": "Solicitud generada por el consumidor prueba 2",
        "prioridad": "media",
    },
    {
        "identificador_externo": "TICKET-001",  
        "tipo_solicitud": "administrativa",
        "nombre_solicitante": "Cliente 3",
        "correo_electronico": "cliente3@gmail.com",
        "descripcion": "Esta solicitud viene con duplicado en su PK ",
        "prioridad": "baja",
    },
    {
        "identificador_externo": "TICKET-004",  
        "tipo_solicitud": "admin",
        "nombre_solicitante": "Cliente 4",
        "correo_electronico": "cliente4@gmail.com",
        "descripcion": "Esta solicitud tiene el campo tipo_solicitud invalido 422",
        "prioridad": "baja",
    },
    {
        "identificador_externo": "TICKET-005",  
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Cliente 5",
        "correo_electronico": "cliente5@gmail",
        "descripcion": "Esta solicitud tiene el campo de correo invalido 422",
        "prioridad": "alta",
    },
    {
        "identificador_externo": "TICKET-006",  
        "tipo_solicitud": "academica",
        "nombre_solicitante": ["Cliente", 6],
        "correo_electronico": "cliente5@gmail.com",
        "descripcion": "Esta solicitud tiene el campo de nombre_solicitante con tipo de dato incorrecto",
        "prioridad": "alta",
    },    
    {
        "identificador_externo": "TICKET-007",  
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Cliente 7",
        "descripcion": "Esta solicitud tiene le falta el campo de correo_electronico",
        "prioridad": "alta",
    }
]


async def procesar_solicitud(api_client: ApiClient, client: httpx.AsyncClient, payload: dict):
    """Envia una solicitud y consulta su estado, sin detener la ejecucion si falla."""
    identificador = payload["identificador_externo"]

    try:
        resultado = await api_client.crear_solicitud(client, payload)
        logger.info(
            "Solicitud creada exitosamente",
            extra={"identificador_externo": identificador, "id": resultado["id"], "estado": resultado["estado"]},
        )

        detalle = await api_client.obtener_solicitud(client, resultado["id"])
        logger.info(
            "Estado consultado",
            extra={"id": detalle["id"], "estado": detalle["estado"]},
        )

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Solicitud rechazada por la API",
            extra={
                "identificador_externo": identificador,
                "status_code": exc.response.status_code,
                "detail": exc.response.text,
            },
        )
    except httpx.RequestError as exc:
        logger.error(
            "Fallo de conexion tras agotar reintentos",
            extra={"identificador_externo": identificador, "error": str(exc)},
        )


async def main():
    api_client = ApiClient(base_url=API_URL, timeout=5.0)

    async with httpx.AsyncClient() as client:
        for payload in SOLICITUDES_DE_PRUEBA:
            await procesar_solicitud(api_client, client, payload)

    logger.info("Ejecucion del consumidor finalizada")


if __name__ == "__main__":
    asyncio.run(main())