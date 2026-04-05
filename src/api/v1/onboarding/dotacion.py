from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models.onboarding import DotacionTemplateRequest, DotacionTemplateResponse
    from utils import ROLE_CARGO_ACCESS, get_current_token_payload
except ImportError:
    from ....models.onboarding import DotacionTemplateRequest, DotacionTemplateResponse
    from ....utils import ROLE_CARGO_ACCESS, get_current_token_payload

router = APIRouter()


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

    user_cargo = token_payload.get("cargo")
    if user_cargo is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    rrhh_cargos = set(ROLE_CARGO_ACCESS.get("rrhh", []))
    can_manage = int(user_cargo) in rrhh_cargos

    if not can_manage:
        try:
            has_team = await db.prepare(
                "SELECT id FROM JERARQUIA WHERE id_jefe_inmediato = ? LIMIT 1"
            ).bind(user_cargo).first()
            can_manage = bool(has_team)
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
