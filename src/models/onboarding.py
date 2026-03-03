from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


class EstadoSolicitud(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En Proceso"
    FINALIZADA = "Finalizada"


class OnboardingRequest(BaseModel):
    """modelo para el request de la solicitud del onboarding"""
    id_empleado: int
    id_area_encargada: str
    fecha_maxima_cumplimiento: datetime
    especificaciones: str | None = None


class OnboardingResponse(BaseModel):
    """Modelo para el response de la solicitud del onboarding"""
    id: int
    id_empleado: int
    id_area_encargada: str
    fecha_creacion: datetime
    fecha_maxima_cumplimiento: datetime
    fecha_fin: datetime | None = None
    estado: EstadoSolicitud
    especificaciones: str | None = None

    model_config = ConfigDict(from_attributes=True)