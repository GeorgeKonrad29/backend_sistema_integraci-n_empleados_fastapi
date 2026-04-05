from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


class EstadoSolicitud(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    FINALIZADO = "Finalizado"


class OnboardingRequest(BaseModel):
    """modelo para el request de la solicitud del onboarding"""
    id_empleado: int
    fecha_fin: datetime
    destinatario: str | None = None
    especificaciones: str | None = None
    estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE


class OnboardingUpdateRequest(BaseModel):
    """modelo para actualización parcial de una solicitud de onboarding"""
    fecha_fin: datetime | None = None
    destinatario: str | None = None
    especificaciones: str | None = None
    estado: EstadoSolicitud | None = None


class OnboardingResponse(BaseModel):
    """Modelo para el response de la solicitud del onboarding"""
    id: int
    id_empleado: int
    fecha_creacion: datetime
    fecha_fin: datetime | None = None
    estado: EstadoSolicitud
    especificaciones: str | None = None
    destinatario: str | None = None
    aviso: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingHistoryResponse(BaseModel):
    """Modelo para eventos del historial de una solicitud"""
    id: int
    id_solicitud: int
    fecha_cambio: datetime
    tipo_cambio: str
    estado_antiguo: str | None = None
    nuevo_estado: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DotacionTemplateRequest(BaseModel):
    """Modelo para crear una plantilla en DOTACION"""
    encargado: str | None = None
    tipo: str | None = "Onboarding"
    especificacion: str


class DotacionTemplateResponse(BaseModel):
    """Modelo de respuesta de plantilla creada en DOTACION"""
    id: int
    encargado: str | None = None
    tipo: str | None = None
    especificacion: str
    aviso: str | None = None

    model_config = ConfigDict(from_attributes=True)