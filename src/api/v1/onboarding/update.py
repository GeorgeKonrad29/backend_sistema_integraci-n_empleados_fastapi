from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _register_history, _row_to_dict

try:
    from models.onboarding import OnboardingResponse, OnboardingUpdateRequest
    from utils import (
        can_update_onboarding_request,
        get_current_token_payload,
        get_payload_cargo,
        require_permission,
    )
except ImportError:
    from ....models.onboarding import OnboardingResponse, OnboardingUpdateRequest
    from ....utils import (
        can_update_onboarding_request,
        get_current_token_payload,
        get_payload_cargo,
        require_permission,
    )

router = APIRouter()

_STATE_FLOW = ["Pendiente", "En proceso", "Finalizado"]


def _next_state(current_state: str) -> str:
    try:
        index = _STATE_FLOW.index(str(current_state))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Estado actual inválido: {current_state}")

    if index >= len(_STATE_FLOW) - 1:
        raise HTTPException(status_code=400, detail="El estado ya está en su valor final")

    return _STATE_FLOW[index + 1]


@router.patch("/{solicitud_id}", response_model=OnboardingResponse)
async def update_onboarding_request(
    solicitud_id: int,
    payload: OnboardingUpdateRequest,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    payload_data = payload.model_dump(exclude_unset=True)
    if not payload_data:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un campo para actualizar")

    try:
        current = await db.prepare(
            """
            SELECT id, id_empleado, fecha_creacion, fecha_fin, estado, especificaciones, destinatario
            FROM SOLICITUDES
            WHERE id = ?
            LIMIT 1
            """
        ).bind(solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitud: {str(e)}")

    if not current:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    current_dict = _clean_row_dict(_row_to_dict(current))

    user_cargo = get_payload_cargo(token_payload)
    destinatario_actual = str(current_dict.get("destinatario") or "").strip().lower()
    can_edit = await can_update_onboarding_request(db, user_cargo, destinatario_actual)
    if not can_edit:
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar esta solicitud")

    next_fecha_fin = payload.fecha_fin.isoformat() if payload.fecha_fin is not None else current_dict.get("fecha_fin")
    next_estado = payload.estado.value if payload.estado is not None else current_dict.get("estado")
    next_especificaciones = (
        payload.especificaciones if "especificaciones" in payload_data else current_dict.get("especificaciones")
    )
    next_destinatario = payload.destinatario if "destinatario" in payload_data else current_dict.get("destinatario")

    cambios: list[tuple[str, str | None, str | None]] = []

    if str(current_dict.get("estado")) != str(next_estado):
        cambios.append(("CAMBIO_ESTADO", str(current_dict.get("estado")), str(next_estado)))

    if str(current_dict.get("fecha_fin")) != str(next_fecha_fin):
        cambios.append(("CAMBIO_FECHA_FIN", str(current_dict.get("fecha_fin")), str(next_fecha_fin)))

    if str(current_dict.get("especificaciones")) != str(next_especificaciones):
        cambios.append(
            (
                "CAMBIO_ESPECIFICACIONES",
                None if current_dict.get("especificaciones") is None else str(current_dict.get("especificaciones")),
                None if next_especificaciones is None else str(next_especificaciones),
            )
        )

    if str(current_dict.get("destinatario")) != str(next_destinatario):
        cambios.append(
            (
                "CAMBIO_DESTINATARIO",
                None if current_dict.get("destinatario") is None else str(current_dict.get("destinatario")),
                None if next_destinatario is None else str(next_destinatario),
            )
        )

    if not cambios:
        return OnboardingResponse.model_validate(current_dict)

    try:
        updated = await db.prepare(
            """
            UPDATE SOLICITUDES
            SET fecha_fin = ?, estado = ?, especificaciones = ?, destinatario = ?
            WHERE id = ?
            RETURNING id, id_empleado, fecha_creacion, fecha_fin, estado, especificaciones, destinatario
            """
        ).bind(next_fecha_fin, next_estado, next_especificaciones, next_destinatario, solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando solicitud: {str(e)}")

    if not updated:
        raise HTTPException(status_code=500, detail="No fue posible actualizar la solicitud")

    try:
        for tipo_cambio, valor_anterior, valor_nuevo in cambios:
            await _register_history(
                db=db,
                id_solicitud=solicitud_id,
                tipo_cambio=tipo_cambio,
                valor_anterior=valor_anterior,
                valor_nuevo=valor_nuevo,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando historial: {str(e)}")

    return OnboardingResponse.model_validate(_clean_row_dict(_row_to_dict(updated)))


@router.post("/solicitudes/{solicitud_id}/estado/siguiente", response_model=OnboardingResponse)
async def advance_onboarding_request_state(
    solicitud_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        current = await db.prepare(
            """
            SELECT id, id_empleado, fecha_creacion, fecha_fin, estado, especificaciones, destinatario
            FROM SOLICITUDES
            WHERE id = ?
            LIMIT 1
            """
        ).bind(solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitud: {str(e)}")

    if not current:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    current_dict = _clean_row_dict(_row_to_dict(current))
    user_cargo = get_payload_cargo(token_payload)
    destinatario_actual = str(current_dict.get("destinatario") or "").strip().lower()
    can_edit = await can_update_onboarding_request(db, user_cargo, destinatario_actual)
    if not can_edit:
        raise HTTPException(status_code=403, detail="No tiene permisos para actualizar esta solicitud")

    estado_actual = str(current_dict.get("estado") or "")
    estado_siguiente = _next_state(estado_actual)

    try:
        updated = await db.prepare(
            """
            UPDATE SOLICITUDES
            SET estado = ?
            WHERE id = ?
            RETURNING id, id_empleado, fecha_creacion, fecha_fin, estado, especificaciones, destinatario
            """
        ).bind(estado_siguiente, solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando estado de solicitud: {str(e)}")

    if not updated:
        raise HTTPException(status_code=500, detail="No fue posible actualizar el estado de la solicitud")

    await _register_history(
        db=db,
        id_solicitud=solicitud_id,
        tipo_cambio="CAMBIO_ESTADO",
        valor_anterior=estado_actual,
        valor_nuevo=estado_siguiente,
    )

    return OnboardingResponse.model_validate(_clean_row_dict(_row_to_dict(updated)))


@router.post("/usuarios/{usuario_id}/estado-onboarding/siguiente")
async def advance_user_onboarding_state(
    usuario_id: int,
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.listar")),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        current = await db.prepare(
            "SELECT id, estado_onboarding FROM USUARIO WHERE id = ? LIMIT 1"
        ).bind(usuario_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo usuario: {str(e)}")

    if not current:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    estado_actual = str(getattr(current, "estado_onboarding", None) or "")
    estado_siguiente = _next_state(estado_actual)

    try:
        updated = await db.prepare(
            """
            UPDATE USUARIO
            SET estado_onboarding = ?
            WHERE id = ?
            RETURNING id, estado_onboarding
            """
        ).bind(estado_siguiente, usuario_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando estado de onboarding del usuario: {str(e)}")

    if not updated:
        raise HTTPException(status_code=500, detail="No fue posible actualizar el estado de onboarding del usuario")

    return {
        "id": updated.id,
        "estado_anterior": estado_actual,
        "estado_actual": updated.estado_onboarding,
    }
