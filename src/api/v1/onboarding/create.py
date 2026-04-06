from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _register_history, _row_to_dict

try:
    from models.onboarding import OnboardingRequest, OnboardingResponse
    from utils import (
        can_create_onboarding_for_employee,
        get_current_token_payload,
        get_payload_cargo,
    )
except ImportError:
    from ....models.onboarding import OnboardingRequest, OnboardingResponse
    from ....utils import (
        can_create_onboarding_for_employee,
        get_current_token_payload,
        get_payload_cargo,
    )

router = APIRouter()


@router.post("/", response_model=OnboardingResponse)
async def create_onboarding_request(
    payload: OnboardingRequest,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Crea una nueva solicitud de onboarding.
    Acceso permitido para RRHH o para el jefe inmediato del empleado.
    Si la plantilla (especificaciones) no existe en DOTACION, se crea y se informa en "aviso".
    """
    env = req.scope["env"]
    db = env.dataBase
    aviso: str | None = None

    try:
        creator_cargo = get_payload_cargo(token_payload)

        user_check = await db.prepare("SELECT id, cargo FROM USUARIO WHERE id = ? LIMIT 1").bind(payload.id_empleado).first()

        if not user_check:
            raise HTTPException(
                status_code=404,
                detail=f"Error: El empleado con ID {payload.id_empleado} no existe."
            )

        empleado_cargo = getattr(user_check, "cargo", None)
        can_create = await can_create_onboarding_for_employee(db, creator_cargo, empleado_cargo)

        if not can_create:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para crear solicitudes para este empleado",
            )

        especificacion = (payload.especificaciones or "").strip()
        if not especificacion:
            raise HTTPException(
                status_code=400,
                detail="La solicitud debe incluir una plantilla en 'especificaciones'",
            )

        template_exists = await db.prepare(
            "SELECT id FROM DOTACION WHERE LOWER(TRIM(especificacion)) = LOWER(TRIM(?)) LIMIT 1"
        ).bind(especificacion).first()

        if not template_exists:
            await db.prepare(
                "INSERT INTO DOTACION (encargado, tipo, especificacion) VALUES (?, ?, ?)"
            ).bind(payload.destinatario, "Onboarding", especificacion).run()
            aviso = "La plantilla no existía en DOTACION y fue creada automáticamente."

        query = """
            INSERT INTO SOLICITUDES (
                id_empleado,
                fecha_creacion,
                fecha_fin,
                estado,
                especificaciones,
                destinatario
            ) VALUES (?, datetime('now'), ?, ?, ?, ?)
            RETURNING *
        """

        result = await db.prepare(query).bind(
            payload.id_empleado,
            payload.fecha_fin.isoformat(),
            payload.estado.value,
            especificacion,
            payload.destinatario
        ).first()

        if not result:
            raise HTTPException(status_code=500, detail="Error al crear la solicitud")

        await _register_history(
            db=db,
            id_solicitud=int(result.id),
            tipo_cambio="CREACION",
            valor_anterior=None,
            valor_nuevo=str(result.estado),
        )

        response_data = _clean_row_dict(_row_to_dict(result))
        response_data["aviso"] = aviso
        return OnboardingResponse.model_validate(response_data)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la base de datos: {str(e)}"
        )
