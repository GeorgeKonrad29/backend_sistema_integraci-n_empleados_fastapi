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
    value = getattr(row, key, None)
    if value is not None:
        return value
    try:
        return row[key]
    except Exception:
        return None


def _serialize_cargo_row(cargo_row):
    return {
        "id": _pick(cargo_row, "id"),
        "nombre_cargo": _pick(cargo_row, "nombre_cargo"),
        "area": _pick(cargo_row, "area"),
        "id_jefe_inmediato": _pick(cargo_row, "id_jefe_inmediato"),
    }


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

        rows_raw = cargos.get("results", []) if isinstance(cargos, dict) else getattr(cargos, "results", [])
        if rows_raw is None:
            rows = []
        elif isinstance(rows_raw, list):
            rows = rows_raw
        else:
            try:
                rows = list(rows_raw)
            except Exception:
                print(f"[auth/cargos] Unexpected rows type: {type(rows_raw).__name__}")
                rows = []

        result_list = []
        for index, cargo_row in enumerate(rows):
            try:
                cargo_dict = _serialize_cargo_row(cargo_row)
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


@router.get("/cargos/{cargo_id}", response_model=JerarquiaResponse)
async def get_cargo_by_id(
    cargo_id: int,
    req: Request,
    token_payload: dict = Security(require_permission("cargos.listar")),
):
    try:
        env = req.scope["env"]
        db = getattr(env, "dataBase", None)
        if db is None:
            print("[auth/cargos/{id}] Missing D1 binding: env.dataBase")
            raise HTTPException(status_code=500, detail="Binding D1 'dataBase' no configurado")

        cargo_row = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA WHERE id = ? LIMIT 1"
        ).bind(cargo_id).first()

        if not cargo_row:
            raise HTTPException(status_code=404, detail=f"Cargo con id={cargo_id} no encontrado")

        return _serialize_cargo_row(cargo_row)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise

        print(f"[auth/cargos/{{id}}] Unhandled error: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error consultando cargo ({type(e).__name__})")
