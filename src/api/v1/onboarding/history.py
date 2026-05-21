from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _row_to_dict, _rows_to_history_response_list

try:
    from models.onboarding import OnboardingHistoryResponse
    from utils import can_view_onboarding_history, get_current_token_payload, get_payload_cargo
except ImportError:
    from ....models.onboarding import OnboardingHistoryResponse
    from ....utils import can_view_onboarding_history, get_current_token_payload, get_payload_cargo

router = APIRouter()


@router.get("/solicitudes/{solicitud_id}/historial", response_model=list[OnboardingHistoryResponse])
async def get_onboarding_request_history(
    solicitud_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    user_cargo = get_payload_cargo(token_payload)

    try:
        solicitud = await db.prepare(
            """
            SELECT s.id, s.id_empleado, s.fecha_creacion, s.fecha_fin, s.estado, s.especificaciones, s.destinatario,
                   u.cargo AS cargo_empleado
            FROM SOLICITUDES s
            JOIN USUARIO u ON u.id = s.id_empleado
            WHERE s.id = ?
              AND s.estado != 'Eliminada'
              AND (u.estado_onboarding IS NULL OR u.estado_onboarding != 'Eliminada')
            LIMIT 1
            """
        ).bind(solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitud: {str(e)}")

    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    solicitud_dict = _clean_row_dict(_row_to_dict(solicitud))
    cargo_empleado = getattr(solicitud, "cargo_empleado", None)

    destinatario_actual = str(solicitud_dict.get("destinatario") or "").strip().lower()
    try:
        can_view = await can_view_onboarding_history(
            db,
            user_cargo,
            destinatario_actual,
            cargo_empleado,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando política de acceso: {str(e)}")

    if not can_view:
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
