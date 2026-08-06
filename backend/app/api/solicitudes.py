from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException,Query
from app.schemas.solicitud import (
    EstadoSolicitud,
    TipoSolicitud,
    PrioridadSolicitud,
    SolicitudCreate,
    SolicitudUpdate,
    SolicitudResponse
)

router = APIRouter()

# para prueba de endpoint antes de hacerla con la bd
SOLICITUDES: list[dict] = []

TRANSICIONES_VALIDAS = {
    EstadoSolicitud.RECIBIDA: {EstadoSolicitud.EN_PROCESO, EstadoSolicitud.RECHAZADA},
    EstadoSolicitud.EN_PROCESO: {EstadoSolicitud.COMPLETADA, EstadoSolicitud.RECHAZADA},
    EstadoSolicitud.COMPLETADA: set(),
    EstadoSolicitud.RECHAZADA: set(),
}


@router.post("/solicitudes", 
        response_model=SolicitudResponse, 
        status_code=201,    
        responses={
        409: {"description": "El identificador externo ya existe"},
        422: {"description": "Datos invalidos o campos faltantes"},
    })
async def crear_solicitud(datos: SolicitudCreate):
    """
    Creacion de una nueva solicitud institucional
    -Primer estado 'Recibida'.
    -Fecha creacion/actualizacion automatica del sistema.
    -Validar identificador externo unico
    """
    for s in SOLICITUDES:
        if s["identificador_externo"] == datos.identificador_externo:
            raise HTTPException(status_code=409, detail="El identificador externo ya existe")

    nuevo_id = SOLICITUDES[-1]["id"] + 1 if SOLICITUDES else 1
    ahora = datetime.now(timezone.utc)

    nueva_solicitud = {
        "id": nuevo_id,
        **datos.model_dump(),
        "estado": EstadoSolicitud.RECIBIDA,
        "fecha_creacion": ahora,
        "fecha_actualizacion": ahora,
    }
    SOLICITUDES.append(nueva_solicitud)
    return nueva_solicitud


@router.get("/solicitudes", response_model=list[SolicitudResponse])
async def listar_solicitudes(
    estado: Optional[EstadoSolicitud] = Query(None, description="Filtro de estado"),
    tipo_solicitud: Optional[TipoSolicitud] = Query(None, description="Filtro tipo"),
    prioridad: Optional[PrioridadSolicitud] = Query(None,description="Filtro prioridad"),
):
    """Consultar el listado de solicitudes.
    
    Opcional aplicar filtros de estado, tipo solicitud y prioridad"""
    resultado = SOLICITUDES

    if estado:
        resultado = [s for s in resultado if s["estado"] == estado]
    if tipo_solicitud:
        resultado = [s for s in resultado if s["tipo_solicitud"] == tipo_solicitud]
    if prioridad:
        resultado = [s for s in resultado if s["prioridad"] == prioridad]

    return resultado


@router.get("/solicitudes/{id}", 
            response_model=SolicitudResponse,
            responses={404: {"description": "Solicitud no encontrada"}},)
async def obtener_solicitud(id: int):
    """Consulta el detalle completo de una solicitud específica por su ID interno."""
    for s in SOLICITUDES:
        if s["id"] == id:
            return s
    raise HTTPException(status_code=404, detail="Solicitud no encontrada")


@router.patch("/solicitudes/{id}/estado", 
            response_model=SolicitudResponse,
            responses={
                404: {"description": "Solicitud no encontrada"},
                422: {"description": "Transición de estado no permitida"},
    },)
async def actualizar_estado(id: int, datos: SolicitudUpdate):
    """
    Actualiza el estado de una solicitud.

    Solo se permiten ciertas transiciones: desde 'recibida' se puede pasar a
    'en_proceso' o 'rechazada'; desde 'en_proceso' se puede pasar a 'completada'
    o 'rechazada'. Los estados 'completada' y 'rechazada' son finales.
    """
    for s in SOLICITUDES:
        if s["id"] == id:
            estado_actual = s["estado"]
            nuevo_estado = datos.estado

            if nuevo_estado not in TRANSICIONES_VALIDAS[estado_actual]:
                raise HTTPException(
                    status_code=422,
                    detail=f"No se puede cambiar de '{estado_actual}' a '{nuevo_estado}'"
                )

            s["estado"] = nuevo_estado
            s["fecha_actualizacion"] = datetime.now(timezone.utc)
            return s
    raise HTTPException(status_code=404, detail="Solicitud no encontrada")