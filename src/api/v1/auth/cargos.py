"""Endpoint para consultar cargos/jerarquía."""
from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models import JerarquiaResponse
    from utils import require_permission
except ImportError:
    from ....models import JerarquiaResponse
    from ....utils import require_permission


router = APIRouter()


def _pick(row, key: str):
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


@router.get("/cargos", response_model=list[JerarquiaResponse])
async def get_cargos(
    req: Request,
    token_payload: dict = Security(require_permission("cargos.listar")),
):
    env = req.scope["env"]
    db = getattr(env, "dataBase", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Binding D1 'dataBase' no configurado")

    try:
        cargos = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA ORDER BY id"
        ).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando cargos: {e}")

    rows = cargos.get("results", []) if isinstance(cargos, dict) else getattr(cargos, "results", [])

    result_list = []
    for cargo_row in rows:
        try:
            cargo_dict = {
                "id": _pick(cargo_row, "id"),
                "nombre_cargo": _pick(cargo_row, "nombre_cargo"),
                "area": _pick(cargo_row, "area"),
                "id_jefe_inmediato": _pick(cargo_row, "id_jefe_inmediato"),
            }
            result_list.append(cargo_dict)
        except Exception:
            pass

    return result_list
