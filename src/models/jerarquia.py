from pydantic import BaseModel


class JerarquiaResponse(BaseModel):
    """Modelo de respuesta para cargos/jerarquía"""
    id: int
    nombre_cargo: str
    area: str
    id_jefe_inmediato: int | None = None
