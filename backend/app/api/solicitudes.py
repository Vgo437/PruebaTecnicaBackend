from typing import Optional
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.solicitud_service import SolicitudService
from fastapi import APIRouter, HTTPException, Query, Depends
from app.schemas.solicitud import (
    EstadoSolicitud,
    TipoSolicitud,
    PrioridadSolicitud,
    SolicitudCreate,
    SolicitudUpdate,
    SolicitudResponse,
)

router = APIRouter(tags=["Solicitudes"])


@router.post("/solicitudes",
        response_model=SolicitudResponse,
        status_code=201,
        responses={
            201: {"description": "Solicitud creada exitosamente"},
            409: {"description": "El identificador externo ya existe"},
            422: {"description": "Datos invalidos o campos faltantes"},
            503: {"description": "Servicio temporalmente no disponible"},
        },)
async def crear_solicitud(datos: SolicitudCreate, db: AsyncSession = Depends(get_db)):
    """
    Creación de una nueva solicitud institucional
    - Primer estado 'Recibida'.
    - Fecha creación/actualización automática del sistema.
    - Valida identificador externo único.
    - Opciones para 'tipo_solicitud': 'acceso_plataforma', 'soporte_tecnico', 'academica'
    - Opciones para 'prioridad': 'baja', 'media', 'alta'
    """
    service = SolicitudService(db)
    return await service.crear_solicitud(datos)


@router.get("/solicitudes", 
        response_model=list[SolicitudResponse],
        responses={
            200: {"description": "Listado de solicitudes obtenido exitosamente"},
            503: {"description": "Servicio temporalmente no disponible"},
        })
async def listar_solicitudes(
    estado: Optional[EstadoSolicitud] = Query(None, description="Filtro de estado: 'recibida', 'en_proceso', 'completada', 'rechazada'"),
    tipo_solicitud: Optional[TipoSolicitud] = Query(None, description="Filtro tipo: 'acceso_plataforma', 'soporte_tecnico', 'academica', 'administrativa'"),
    prioridad: Optional[PrioridadSolicitud] = Query(None, description="Filtro prioridad: 'baja', 'media', 'alta'"),
    db: AsyncSession = Depends(get_db),
):
    """Consultar el listado de solicitudes, con filtros opcionales de estado, tipo y prioridad."""
    service = SolicitudService(db)
    return await service.listar_solicitudes(estado, tipo_solicitud, prioridad)


@router.get("/solicitudes/{id}",
        response_model=SolicitudResponse,
        responses={
            200: {"description": "Solicitud encontrada"},
            404: {"description": "Solicitud no encontrada"},
            503: {"description": "Servicio temporalmente no disponible"},
        },)
async def obtener_solicitud(id: int, db: AsyncSession = Depends(get_db)):
    """Consulta el detalle completo de una solicitud específica por su ID interno."""
    service = SolicitudService(db)
    return await service.obtener_solicitud(id)


@router.patch("/solicitudes/{id}/estado",
        response_model=SolicitudResponse,
        responses={
            200: {"description": "Estado actualizado exitosamente"},
            404: {"description": "Solicitud no encontrada"},
            422: {"description": "Transición de estado no permitida"},
            503: {"description": "Servicio temporalmente no disponible"},
        }
)
async def actualizar_estado(id: int, datos: SolicitudUpdate, db: AsyncSession = Depends(get_db)):
    """
    Actualiza el estado de una solicitud.

    Solo se permiten ciertas transiciones: desde 'recibida' se puede pasar a
    'en_proceso' o 'rechazada'; desde 'en_proceso' se puede pasar a 'completada'
    o 'rechazada'. Los estados 'completada' y 'rechazada' son finales.
    """
    service = SolicitudService(db)
    return await service.actualizar_estado(id, datos.estado)