"""Endpoint para consultar cargos/jerarquía."""
from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models import JerarquiaResponse
    from utils import require_permission
except ImportError:
    from ....models import JerarquiaResponse
    from ....utils import require_permission


router = APIRouter()


@router.get("/cargos", response_model=list[JerarquiaResponse])
async def get_cargos(
    req: Request,
    token_payload: dict = Security(require_permission("cargos.listar")),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        cargos = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA ORDER BY id"
        ).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando cargos: {e}")

    result_list = []
    for cargo_row in cargos.results:
        try:
            cargo_dict = {
                "id": cargo_row.id,
                "nombre_cargo": cargo_row.nombre_cargo,
                "area": cargo_row.area,
                "id_jefe_inmediato": cargo_row.id_jefe_inmediato,
            }
            result_list.append(cargo_dict)
        except Exception:
            pass

    return result_list
