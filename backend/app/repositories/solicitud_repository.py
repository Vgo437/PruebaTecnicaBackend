from typing import Optional
from sqlalchemy import select
from app.models.solicitud import Solicitud
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.solicitud import (
    EstadoSolicitud,
    TipoSolicitud,
    PrioridadSolicitud,
)


class SolicitudRepository:
    """Encapsula el acceso a datos de la tabla 'solicitudes'."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_identificador_externo(self, identificador_externo: str) -> Optional[Solicitud]:
        """Busca una solicitud por su identificador externo (usado para detectar duplicados)."""
        result = await self.db.execute(
            select(Solicitud).where(Solicitud.identificador_externo == identificador_externo)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id: int) -> Optional[Solicitud]:
        """Busca una solicitud por su ID interno."""
        result = await self.db.execute(select(Solicitud).where(Solicitud.id == id))
        return result.scalar_one_or_none()

    async def list(
        self,
        estado: Optional[EstadoSolicitud] = None,
        tipo_solicitud: Optional[TipoSolicitud] = None,
        prioridad: Optional[PrioridadSolicitud] = None,
    ) -> list[Solicitud]:
        """Lista solicitudes, aplicando filtros opcionales."""
        query = select(Solicitud)

        if estado:
            query = query.where(Solicitud.estado == estado)
        if tipo_solicitud:
            query = query.where(Solicitud.tipo_solicitud == tipo_solicitud)
        if prioridad:
            query = query.where(Solicitud.prioridad == prioridad)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, solicitud: Solicitud) -> Solicitud:
        """Inserta una nueva solicitud. Puede lanzar IntegrityError si el identificador_externo ya existe."""
        self.db.add(solicitud)
        await self.db.commit()
        await self.db.refresh(solicitud)
        return solicitud

    async def update_estado(self, solicitud: Solicitud, nuevo_estado: EstadoSolicitud) -> Solicitud:
        """Actualiza el estado de una solicitud existente."""
        solicitud.estado = nuevo_estado
        await self.db.commit()
        await self.db.refresh(solicitud)
        return solicitud