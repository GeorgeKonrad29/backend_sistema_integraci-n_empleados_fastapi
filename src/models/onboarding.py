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


class OnboardingResponse(BaseModel):
    """Modelo para el response de la solicitud del onboarding"""
    id: int
    id_empleado: int
    fecha_creacion: datetime
    fecha_fin: datetime | None = None
    estado: EstadoSolicitud
    especificaciones: str | None = None
    destinatario: str | None = None

    model_config = ConfigDict(from_attributes=True)