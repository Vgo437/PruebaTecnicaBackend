import os
import sys
import uuid
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
id_duplicado = f"TICKET-{uuid.uuid4().hex[:8]}"

SOLICITUDES_DE_PRUEBA = [
    {
        "identificador_externo": f"TICKET-{uuid.uuid4().hex[:8]}",
        "tipo_solicitud": "soporte_tecnico",
        "nombre_solicitante": "Cliente 1",
        "correo_electronico": "cliente1@gmail.com",
        "descripcion": "Solicitud generada por el consumidor prueba 1",
        "prioridad": "alta",
    },
    {
        "identificador_externo": f"TICKET-{uuid.uuid4().hex[:8]}",
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Cliente 2",
        "correo_electronico": "cliente2@gmail.com",
        "descripcion": "Solicitud generada por el consumidor prueba 2",
        "prioridad": "media",
    },
    {
        "identificador_externo": f"TICKET-{uuid.uuid4().hex[:8]}",  
        "tipo_solicitud": "administrativa",
        "nombre_solicitante": ["Cliente", 6],
        "correo_electronico": "cliente3@gmail.com",
        "descripcion": "Solicitud prueba 3 formato invalido en nombre",
        "prioridad": "baja",
    },
    {
        "identificador_externo": f"TICKET-{uuid.uuid4().hex[:8]}",  
        "tipo_solicitud": "admin",
        "nombre_solicitante": "Cliente 4",
        "correo_electronico": "cliente4@gmail.com",
        "descripcion": "Esta solicitud tiene el campo tipo_solicitud invalido 422",
        "prioridad": "baja",
    },
    {
        "identificador_externo": f"TICKET-{uuid.uuid4().hex[:8]}",  
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Cliente 5",
        "correo_electronico": "cliente5@gmail",
        "descripcion": "Esta solicitud tiene el campo de correo invalido 422",
        "prioridad": "alta",
    },
    {
        "identificador_externo": id_duplicado,  
        "tipo_solicitud": "academica",
        "nombre_solicitante": "cliente 6",
        "correo_electronico": "cliente6@gmail.com",
        "descripcion": "EstaEsta solicitud viene con duplicado en su PK ",
        "prioridad": "alta",
    },    
    {
        "identificador_externo": id_duplicado,  
        "tipo_solicitud": "academica",
        "nombre_solicitante": "Cliente 7",
        "correo_electronico": "cliente6@gmail.com",
        "descripcion": "EstaEsta solicitud viene con duplicado en su PK ",
        "prioridad": "alta",
    }
]


async def procesar_solicitud(api_client: ApiClient, client: httpx.AsyncClient, payload: dict):
    """Envia una solicitud y consulta su estado, sin detener la ejecucion si falla."""
    identificador = payload["identificador_externo"]
    request_id = str(uuid.uuid4())

    try:
        resultado = await api_client.crear_solicitud(client, payload, request_id)
        logger.info(
            "Solicitud creada exitosamente",
            extra={
                "request_id": request_id,
                "identificador_externo": identificador,
                "id": resultado["id"],
                "estado": resultado["estado"],
            },
        )

        detalle = await api_client.obtener_solicitud(client, resultado["id"], request_id)
        logger.info(
            "Estado consultado",
            extra={"request_id": request_id, "id": detalle["id"], "estado": detalle["estado"]},
        )

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Solicitud rechazada por la API",
            extra={
                "request_id": request_id,
                "identificador_externo": identificador,
                "status_code": exc.response.status_code,
                "detail": exc.response.text,
            },
        )
    except httpx.RequestError as exc:
        logger.error(
            "Fallo de conexion tras agotar reintentos",
            extra={"request_id": request_id, "identificador_externo": identificador, "error": str(exc)},
        )
        
async def main():
    api_client = ApiClient(base_url=API_URL, timeout=5.0)

    async with httpx.AsyncClient() as client:
        for payload in SOLICITUDES_DE_PRUEBA:
            await procesar_solicitud(api_client, client, payload)

    logger.info("Ejecucion del consumidor finalizada")


if __name__ == "__main__":
    asyncio.run(main())