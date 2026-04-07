"""Endpoint para consultar cargos/jerarquía."""
import traceback

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
    try:
        env = req.scope["env"]
        db = getattr(env, "dataBase", None)
        if db is None:
            print("[auth/cargos] Missing D1 binding: env.dataBase")
            raise HTTPException(status_code=500, detail="Binding D1 'dataBase' no configurado")

        cargos = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA ORDER BY id"
        ).all()

        rows = cargos.get("results", []) if isinstance(cargos, dict) else getattr(cargos, "results", [])
        if not isinstance(rows, list):
            print(f"[auth/cargos] Unexpected rows type: {type(rows).__name__}")
            rows = []

        result_list = []
        for index, cargo_row in enumerate(rows):
            try:
                cargo_dict = {
                    "id": _pick(cargo_row, "id"),
                    "nombre_cargo": _pick(cargo_row, "nombre_cargo"),
                    "area": _pick(cargo_row, "area"),
                    "id_jefe_inmediato": _pick(cargo_row, "id_jefe_inmediato"),
                }
                result_list.append(cargo_dict)
            except Exception as row_error:
                print(
                    f"[auth/cargos] Row parse error at index={index}: "
                    f"{type(row_error).__name__}: {row_error}"
                )

        return result_list
    except Exception as e:
        if isinstance(e, HTTPException):
            raise

        print(f"[auth/cargos] Unhandled error: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error consultando cargos ({type(e).__name__})")
