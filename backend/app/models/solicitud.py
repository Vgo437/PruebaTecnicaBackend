from app.db.base import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from app.schemas.solicitud import TipoSolicitud, EstadoSolicitud, PrioridadSolicitud


class Solicitud(Base):
    """Representa la tabla 'solicitudes' en PostgreSQL.
    
    - Columnas como tipo_solicitud, prioridad y estado, vienen de las clases que usan Enum de los schemas de pydantic como doble validacion.
    - fecha_creacion y fecha_actualizacion se crean automaticamente
    """

    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    identificador_externo = Column(String, unique=True, nullable=False, index=True)
    tipo_solicitud = Column(SQLEnum(TipoSolicitud), nullable=False, index=True)
    nombre_solicitante = Column(String, nullable=False)
    correo_electronico = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    prioridad = Column(SQLEnum(PrioridadSolicitud), nullable=False, index=True)
    estado = Column(SQLEnum(EstadoSolicitud), nullable=False, default=EstadoSolicitud.RECIBIDA, index=True)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )