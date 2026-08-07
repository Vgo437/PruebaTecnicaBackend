from typing import Optional
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.solicitud import Solicitud
from app.repositories.solicitud_repository import SolicitudRepository
from app.schemas.solicitud import (
    SolicitudCreate,
    EstadoSolicitud,
    TipoSolicitud,
    PrioridadSolicitud,
)

# Transiciones de estado permitidas
TRANSICIONES_VALIDAS = {
    EstadoSolicitud.RECIBIDA: {EstadoSolicitud.EN_PROCESO, EstadoSolicitud.RECHAZADA},
    EstadoSolicitud.EN_PROCESO: {EstadoSolicitud.COMPLETADA, EstadoSolicitud.RECHAZADA},
    EstadoSolicitud.COMPLETADA: set(),
    EstadoSolicitud.RECHAZADA: set(),
}


class SolicitudService:
    """Contiene la lógica de negocio para la gestión de solicitudes."""

    def __init__(self, db: AsyncSession):
        self.repo = SolicitudRepository(db)

    async def crear_solicitud(self, datos: SolicitudCreate) -> Solicitud:
        """Crea una nueva solicitud, validando que el identificador externo no exista."""
        nueva_solicitud = Solicitud(
            **datos.model_dump(),
            estado=EstadoSolicitud.RECIBIDA,
        )
        try:
            return await self.repo.create(nueva_solicitud)
        except IntegrityError:
            raise HTTPException(status_code=409, detail="El identificador externo ya existe")

    async def listar_solicitudes(
        self,
        estado: Optional[EstadoSolicitud] = None,
        tipo_solicitud: Optional[TipoSolicitud] = None,
        prioridad: Optional[PrioridadSolicitud] = None,
    ) -> list[Solicitud]:
        """Lista solicitudes aplicando filtros opcionales."""
        return await self.repo.list(estado, tipo_solicitud, prioridad)

    async def obtener_solicitud(self, id: int) -> Solicitud:
        """Obtiene una solicitud por ID, o lanza 404 si no existe."""
        solicitud = await self.repo.get_by_id(id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        return solicitud

    async def actualizar_estado(self, id: int, nuevo_estado: EstadoSolicitud) -> Solicitud:
        """Actualiza el estado de una solicitud, validando que la transición sea permitida."""
        solicitud = await self.repo.get_by_id(id)
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if nuevo_estado not in TRANSICIONES_VALIDAS[solicitud.estado]:
            raise HTTPException(
                status_code=422,
                detail=f"No se puede cambiar de '{solicitud.estado.value}' a '{nuevo_estado.value}'"
            )

        return await self.repo.update_estado(solicitud, nuevo_estado)