from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _row_to_dict, _rows_to_history_response_list

try:
    from models.onboarding import OnboardingHistoryResponse
    from utils import ROLE_CARGO_ACCESS, get_current_token_payload
except ImportError:
    from ....models.onboarding import OnboardingHistoryResponse
    from ....utils import ROLE_CARGO_ACCESS, get_current_token_payload

router = APIRouter()


@router.get("/solicitudes/{solicitud_id}/historial", response_model=list[OnboardingHistoryResponse])
async def get_onboarding_request_history(
    solicitud_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    user_cargo = token_payload.get("cargo")
    if user_cargo is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    try:
        solicitud = await db.prepare(
            """
            SELECT s.id, s.id_empleado, s.fecha_creacion, s.fecha_fin, s.estado, s.especificaciones, s.destinatario,
                   u.cargo AS cargo_empleado
            FROM SOLICITUDES s
            JOIN USUARIO u ON u.id = s.id_empleado
            WHERE s.id = ?
            LIMIT 1
            """
        ).bind(solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitud: {str(e)}")

    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    solicitud_dict = _clean_row_dict(_row_to_dict(solicitud))
    cargo_empleado = getattr(solicitud, "cargo_empleado", None)

    try:
        cargo_info = await db.prepare(
            "SELECT nombre_cargo, area FROM JERARQUIA WHERE id = ? LIMIT 1"
        ).bind(user_cargo).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo cargo del usuario: {str(e)}")

    if not cargo_info:
        raise HTTPException(status_code=404, detail="No se encontró el cargo del usuario en jerarquía")

    nombre_cargo = str(cargo_info.nombre_cargo or "").strip().lower()
    area = str(cargo_info.area or "").strip().lower()
    destinatario_actual = str(solicitud_dict.get("destinatario") or "").strip().lower()
    rrhh_cargos = set(ROLE_CARGO_ACCESS.get("rrhh", []))

    is_rrhh = int(user_cargo) in rrhh_cargos
    is_destinatario = destinatario_actual and destinatario_actual in {nombre_cargo, area}

    is_direct_boss = False
    if cargo_empleado is not None:
        try:
            jefe_info = await db.prepare(
                "SELECT id_jefe_inmediato FROM JERARQUIA WHERE id = ? LIMIT 1"
            ).bind(cargo_empleado).first()
            is_direct_boss = bool(jefe_info and getattr(jefe_info, "id_jefe_inmediato", None) == int(user_cargo))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error validando jerarquía: {str(e)}")

    if not (is_rrhh or is_destinatario or is_direct_boss):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver el historial de esta solicitud")

    try:
        historial_result = await db.prepare(
            """
            SELECT id, id_solicitud, fecha_cambio, tipo_cambio, estado_antiguo, nuevo_estado
            FROM HISTORIAL
            WHERE id_solicitud = ?
            ORDER BY fecha_cambio DESC
            """
        ).bind(solicitud_id).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

    return _rows_to_history_response_list(historial_result.results)
