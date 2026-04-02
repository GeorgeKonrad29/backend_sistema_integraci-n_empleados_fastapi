from pydantic import BaseModel, Field


class PuestoTrabajoAsignacionRequest(BaseModel):
    id_empleado: int | None = None
    piso: int = Field(..., ge=1, le=2)
    fila: int = Field(..., ge=1, le=20)
    columna: int = Field(..., ge=1, le=20)
    tipo_puesto: str | None = None


class PuestoTrabajoResponse(BaseModel):
    id: int
    id_empleado: int | None = None
    coordenadas: str
    piso: int
    fila: int
    columna: int
    tipo_puesto: str | None = None
