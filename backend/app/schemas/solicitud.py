from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class TipoSolicitud(str, Enum):
    ACCESO_PLATAFORMA = "acceso_plataforma"
    SOPORTE_TECNICO = "soporte_tecnico"
    ACADEMICA = "academica"
    ADMINISTRATIVA = "administrativa"


class EstadoSolicitud(str, Enum):
    RECIBIDA = "recibida"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    RECHAZADA = "rechazada"


class PrioridadSolicitud(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class SolicitudCreate(BaseModel):
    """Datos requeridos para crear una solicitud"""
    identificador_externo: str = Field(..., min_length=1,description="Codigo unico que viene del sistema de origen")
    tipo_solicitud: TipoSolicitud = Field(..., description="Tipo de solicitud, ejm: 'acceso plataforma','academica',etc.")
    nombre_solicitante: str = Field(..., min_length=1, description="Nombre de la persona que realiza la solicitud")
    correo_electronico: EmailStr = Field(...,description="Correo de la persona, en formato valido")
    descripcion: str = Field(..., min_length=1, description="Detalle del requerimiento")
    prioridad: PrioridadSolicitud = Field(...,description="Nivel de atencion, ejm: 'baja', 'media', 'alta'")


class SolicitudUpdate(BaseModel):
    """Campo permitido para actualizacion"""
    estado: EstadoSolicitud = Field(..., description="Nuevo estado de la solicitud, ejm: (recibida, en_proceso, completada, rechazada)")


class SolicitudResponse(BaseModel):
    """Estructura completa de una solicitud, incluyendo los campos generados por el sistema (id, estado, fechas)."""
    id: int
    identificador_externo: str
    tipo_solicitud: TipoSolicitud
    nombre_solicitante: str
    correo_electronico: EmailStr
    descripcion: str
    prioridad: PrioridadSolicitud
    estado: EstadoSolicitud
    fecha_creacion: datetime
    fecha_actualizacion: datetime