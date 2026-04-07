"""Endpoint para consultar cargos/jerarquía."""
from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models import JerarquiaResponse
    from utils import get_current_token_payload
except ImportError:
    from ....models import JerarquiaResponse
    from ....utils import get_current_token_payload


router = APIRouter()


def _clean_row_dict(row_dict: dict) -> dict:
    clean_dict = {}
    for key, value in row_dict.items():
        if str(value) == "jsnull" or value is None:
            clean_dict[key] = None
        else:
            clean_dict[key] = value
    return clean_dict


def _row_to_cargo_response(row) -> dict:
    if hasattr(row, "to_py"):
        row_dict = row.to_py()
    else:
        row_dict = {
            "id": getattr(row, "id", None),
            "nombre_cargo": getattr(row, "nombre_cargo", None),
            "area": getattr(row, "area", None),
            "id_jefe_inmediato": getattr(row, "id_jefe_inmediato", None),
        }

    return _clean_row_dict(
        {
            "id": row_dict.get("id"),
            "nombre_cargo": row_dict.get("nombre_cargo"),
            "area": row_dict.get("area"),
            "id_jefe_inmediato": row_dict.get("id_jefe_inmediato"),
        }
    )


@router.get("/cargos", response_model=list[JerarquiaResponse])
async def get_cargos(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        query_result = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA ORDER BY id"
        ).all()
        return [_row_to_cargo_response(row) for row in query_result.results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando cargos: {str(e)}")


@router.get("/cargos/{cargo_id}", response_model=JerarquiaResponse)
async def get_cargo_by_id(
    cargo_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        cargo_row = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA WHERE id = ? LIMIT 1"
        ).bind(cargo_id).first()

        if not cargo_row:
            raise HTTPException(status_code=404, detail=f"Cargo con id={cargo_id} no encontrado")

        return _row_to_cargo_response(cargo_row)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error consultando cargo: {str(e)}")
