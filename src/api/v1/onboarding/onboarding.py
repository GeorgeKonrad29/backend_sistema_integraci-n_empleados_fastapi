from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models.onboarding import OnboardingRequest, OnboardingResponse
    from utils import get_current_token_payload, require_permission
except ImportError:
    from ....models.onboarding import OnboardingRequest, OnboardingResponse
    from ....utils import get_current_token_payload, require_permission

router = APIRouter()


def _clean_row_dict(row_dict: dict) -> dict:
    clean_dict = {}
    for key, value in row_dict.items():
        if str(value) == "jsnull" or value is None:
            clean_dict[key] = None
        else:
            clean_dict[key] = value
    return clean_dict


def _row_to_dict(row) -> dict:
    if hasattr(row, "to_py"):
        return row.to_py()

    return {
        "id": row.id,
        "id_empleado": row.id_empleado,
        "fecha_creacion": row.fecha_creacion,
        "fecha_fin": row.fecha_fin,
        "estado": row.estado,
        "especificaciones": row.especificaciones,
        "destinatario": row.destinatario,
    }


def _rows_to_onboarding_response_list(rows) -> list[dict]:
    final_list = []
    for row in rows:
        final_list.append(_clean_row_dict(_row_to_dict(row)))
    return final_list


@router.post("/", response_model=OnboardingResponse)
async def create_onboarding_request(
    payload: OnboardingRequest,
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.crear")),
):
    """
    Crea una nueva solicitud de onboarding. Protegido. Solo usuarios con cargo 1, 7 o 24.
    """
    env = req.scope["env"]
    db = env.dataBase

    try:
        # Verificar si el empleado existe
        user_check = await db.prepare("SELECT id FROM USUARIO WHERE id = ?").bind(payload.id_empleado).first()
        
        if not user_check:
            raise HTTPException(
                status_code=404, 
                detail=f"Error: El empleado con ID {payload.id_empleado} no existe."
            )

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
            payload.especificaciones,
            payload.destinatario
        ).first()

        if not result:
            raise HTTPException(status_code=500, detail="Error al crear la solicitud")

        return OnboardingResponse.model_validate(_clean_row_dict(_row_to_dict(result)))

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error en la base de datos: {str(e)}"
        )


@router.get("/", response_model=list[OnboardingResponse])
async def list_onboarding_requests(
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.listar")),
):
    """
    Lista todas las solicitudes de onboarding. Protegido. Solo usuarios con cargo 1, 7 o 24.
    """
    env = req.scope["env"]
    db = env.dataBase

    try:
        query_result = await db.prepare("SELECT * FROM SOLICITUDES ORDER BY fecha_creacion DESC").all()
        
        return _rows_to_onboarding_response_list(query_result.results)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener solicitudes: {str(e)}"
        )


@router.get("/solicitudes-equipo", response_model=list[OnboardingResponse])
async def list_team_onboarding_requests(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Lista las solicitudes de onboarding de los empleados cuyo cargo reporta
    directamente al cargo del usuario logueado.
    """
    env = req.scope["env"]
    db = env.dataBase

    cargo_jefe = token_payload.get("cargo")
    if cargo_jefe is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    try:
        query_result = await db.prepare(
            """
            SELECT s.id, s.id_empleado, s.fecha_creacion, s.fecha_fin, s.estado, s.especificaciones, s.destinatario
            FROM SOLICITUDES s
            JOIN USUARIO u ON u.id = s.id_empleado
            JOIN JERARQUIA j ON j.id = u.cargo
            WHERE j.id_jefe_inmediato = ?
            ORDER BY s.fecha_creacion DESC
            """
        ).bind(cargo_jefe).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener solicitudes del equipo: {str(e)}")

    return _rows_to_onboarding_response_list(query_result.results)