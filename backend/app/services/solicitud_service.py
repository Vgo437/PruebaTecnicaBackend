from typing import Optional
from sqlalchemy.exc import IntegrityError
from app.models.solicitud import Solicitud
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.solicitud_repository import SolicitudRepository
from app.core.domain_exceptions import (
    SolicitudNoEncontrada,
    IdentificadorDuplicado,
    TransicionInvalida,
)
from app.schemas.solicitud import (
    SolicitudCreate,
    EstadoSolicitud,
    TipoSolicitud,
    PrioridadSolicitud,
)

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
            raise IdentificadorDuplicado()

    async def listar_solicitudes(
        self,
        estado: Optional[EstadoSolicitud] = None,
        tipo_solicitud: Optional[TipoSolicitud] = None,
        prioridad: Optional[PrioridadSolicitud] = None,
    ) -> list[Solicitud]:
        """Lista solicitudes aplicando filtros opcionales."""
        return await self.repo.list(estado, tipo_solicitud, prioridad)

    async def obtener_solicitud(self, id: int) -> Solicitud:
        """Obtiene una solicitud por ID, o lanza excepcion de dominio si no existe."""
        solicitud = await self.repo.get_by_id(id)
        if not solicitud:
            raise SolicitudNoEncontrada()
        return solicitud

    async def actualizar_estado(self, id: int, nuevo_estado: EstadoSolicitud) -> Solicitud:
        """Actualiza el estado de una solicitud, validando que la transición sea permitida."""
        solicitud = await self.repo.get_by_id(id)
        if not solicitud:
            raise SolicitudNoEncontrada()

        if nuevo_estado not in TRANSICIONES_VALIDAS[solicitud.estado]:
            raise TransicionInvalida(solicitud.estado, nuevo_estado)

        return await self.repo.update_estado(solicitud, nuevo_estado)