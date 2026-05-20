from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models.onboarding import DotacionTemplateRequest, DotacionTemplateResponse
    from utils import can_manage_dotacion, get_current_token_payload, get_payload_cargo
    from utils import require_permission
except ImportError:
    from ....models.onboarding import DotacionTemplateRequest, DotacionTemplateResponse
    from ....utils import can_manage_dotacion, get_current_token_payload, get_payload_cargo
    from ....utils import require_permission

router = APIRouter()


def _row_to_dotacion_response(row) -> dict:
    if hasattr(row, "to_py"):
        row_dict = row.to_py()
    else:
        row_dict = {
            "id": getattr(row, "id", None),
            "encargado": getattr(row, "encargado", None),
            "tipo": getattr(row, "tipo", None),
            "especificacion": getattr(row, "especificacion", None),
        }

    return {
        "id": row_dict.get("id"),
        "encargado": row_dict.get("encargado"),
        "tipo": row_dict.get("tipo"),
        "especificacion": row_dict.get("especificacion"),
    }


@router.get("/dotacion", response_model=list[DotacionTemplateResponse])
async def list_dotacion_templates(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Obtiene todos los registros de DOTACION.
    """
    env = req.scope["env"]
    db = env.dataBase

    try:
        result = await db.prepare(
            "SELECT id, encargado, tipo, especificacion FROM DOTACION ORDER BY id DESC"
        ).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando DOTACION: {str(e)}")

    return [DotacionTemplateResponse.model_validate(_row_to_dotacion_response(row)) for row in result.results]

@router.post("/dotacion", response_model=DotacionTemplateResponse)
async def create_dotacion_template(
    payload: DotacionTemplateRequest,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Crea una plantilla en DOTACION.
    Acceso permitido para RRHH o cargos que sean jefe inmediato de al menos un cargo.
    """
    env = req.scope["env"]
    db = env.dataBase

    user_cargo = get_payload_cargo(token_payload)

    try:
        can_manage = await can_manage_dotacion(db, user_cargo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando jerarquía: {str(e)}")

    if not can_manage:
        raise HTTPException(status_code=403, detail="No tiene permisos para crear plantillas en DOTACION")

    especificacion = (payload.especificacion or "").strip()
    if not especificacion:
        raise HTTPException(status_code=400, detail="La especificación no puede estar vacía")

    try:
        existing = await db.prepare(
            "SELECT id, encargado, tipo, especificacion FROM DOTACION WHERE LOWER(TRIM(especificacion)) = LOWER(TRIM(?)) LIMIT 1"
        ).bind(especificacion).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando DOTACION: {str(e)}")

    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una plantilla con esa especificación")

    encargado = (payload.encargado or "").strip() or None
    tipo = (payload.tipo or "").strip() or "Onboarding"

    try:
        created = await db.prepare(
            "INSERT INTO DOTACION (encargado, tipo, especificacion) VALUES (?, ?, ?) RETURNING id, encargado, tipo, especificacion"
        ).bind(encargado, tipo, especificacion).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando plantilla en DOTACION: {str(e)}")

    if not created:
        raise HTTPException(status_code=500, detail="No se pudo crear la plantilla en DOTACION")

    return DotacionTemplateResponse.model_validate(
        {
            "id": int(created.id),
            "encargado": created.encargado,
            "tipo": created.tipo,
            "especificacion": created.especificacion,
            "aviso": "Plantilla creada correctamente en DOTACION.",
        }
    )
