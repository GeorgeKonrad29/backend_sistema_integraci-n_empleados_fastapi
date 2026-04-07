import json
from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _register_history, _row_to_dict

try:
    from utils.resend import fetch as fetch_resend_api_key
except ImportError:
    from ....utils.resend import fetch as fetch_resend_api_key

try:
    from models.onboarding import OnboardingResponse, OnboardingUpdateRequest
    from utils import (
        can_update_onboarding_request,
        get_current_token_payload,
        get_payload_cargo,
    )
except ImportError:
    from ....models.onboarding import OnboardingResponse, OnboardingUpdateRequest
    from ....utils import (
        can_update_onboarding_request,
        get_current_token_payload,
        get_payload_cargo,
    )

router = APIRouter()

_STATE_FLOW = ["Pendiente", "En proceso", "Finalizado"]
RESEND_FROM_EMAIL = "onboarding@resend.dev"
TEST_RECIPIENT_EMAIL = "jorgeluis57134@gmail.com"


def _resolve_resend_from_email(req: Request) -> str:
    env = req.scope["env"]
    configured = getattr(env, "RESEND_FROM_EMAIL", None)
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return RESEND_FROM_EMAIL


async def _get_receiver_user(db, user_id: int | None) -> dict | None:
    if user_id is None:
        return None

    try:
        user_row = await db.prepare(
            "SELECT id, nombre, correo, rol, cargo FROM USUARIO WHERE id = ? LIMIT 1"
        ).bind(int(user_id)).first()
    except Exception:
        return None

    if not user_row:
        return None

    user_dict = _clean_row_dict(_row_to_dict(user_row))
    user_dict["nombre"] = getattr(user_row, "nombre", None)
    user_dict["correo"] = getattr(user_row, "correo", None)
    user_dict["rol"] = getattr(user_row, "rol", None)
    user_dict["cargo"] = getattr(user_row, "cargo", None)
    return user_dict


async def _send_en_proceso_notification_email(
    req: Request,
    solicitud: dict,
    receiver_user: dict | None,
    encargado_role: str,
    encargado_name: str,
) -> bool:
    try:
        env = req.scope["env"]
        resend_api_key = await fetch_resend_api_key(req, env)
    except Exception:
        return False

    from_email = _resolve_resend_from_email(req)
    to_email = TEST_RECIPIENT_EMAIL
    if not resend_api_key or not from_email or not to_email:
        return False

    try:
        from pyodide.http import pyfetch
    except Exception:
        return False

    receiver_name = None if not receiver_user else receiver_user.get("nombre")
    receiver_email = None if not receiver_user else receiver_user.get("correo")
    receiver_role = None if not receiver_user else receiver_user.get("rol")
    receiver_id = None if not receiver_user else receiver_user.get("id")

    email_payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Solicitud actualizada a En proceso",
        "html": (
            "<p>Una solicitud cambió al estado <strong>En proceso</strong>.</p>"
            "<p><strong>Encargado</strong><br>"
            f"Rol: {encargado_role}<br>"
            f"Nombre: {encargado_name}</p>"
            "<p><strong>Datos de la solicitud</strong><br>"
            f"ID: {solicitud.get('id')}<br>"
            f"ID Empleado: {solicitud.get('id_empleado')}<br>"
            f"Fecha creación: {solicitud.get('fecha_creacion')}<br>"
            f"Fecha fin: {solicitud.get('fecha_fin')}<br>"
            f"Estado: {solicitud.get('estado')}<br>"
            f"Especificaciones: {solicitud.get('especificaciones')}<br>"
            f"Destinatario: {solicitud.get('destinatario')}</p>"
            "<p><strong>Usuario que debe recibirla</strong><br>"
            f"ID: {receiver_id}<br>"
            f"Nombre: {receiver_name}<br>"
            f"Correo: {receiver_email}<br>"
            f"Rol: {receiver_role}</p>"
        ),
    }

    try:
        response = await pyfetch(
            "https://api.resend.com/emails",
            method="POST",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            body=json.dumps(email_payload),
        )

        if response.status in [200, 201, 202]:
            return True

        try:
            body_text = await response.text()
        except Exception:
            body_text = "<sin cuerpo>"

        print(
            f"[onboarding/update] En-proceso notification rejected. status={response.status} "
            f"from={from_email} to={to_email} body={body_text}"
        )
        return False
    except Exception:
        return False


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

    updated_dict = _clean_row_dict(_row_to_dict(updated))
    notify_en_proceso = str(current_dict.get("estado")) != "En proceso" and str(updated_dict.get("estado")) == "En proceso"
    if notify_en_proceso:
        receiver_user = await _get_receiver_user(db, updated_dict.get("id_empleado"))
        notification_sent = await _send_en_proceso_notification_email(
            req=req,
            solicitud=updated_dict,
            receiver_user=receiver_user,
            encargado_role=str(token_payload.get("rol") or "No definido"),
            encargado_name=str(token_payload.get("nombre") or token_payload.get("correo") or "No definido"),
        )
        if not notification_sent:
            print(f"[onboarding/update] En-proceso notification not sent for solicitud_id={solicitud_id}")

    return OnboardingResponse.model_validate(updated_dict)


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
    updated_dict = _clean_row_dict(_row_to_dict(updated))

    if str(estado_siguiente) == "En proceso":
        receiver_user = await _get_receiver_user(db, updated_dict.get("id_empleado"))
        notification_sent = await _send_en_proceso_notification_email(
            req=req,
            solicitud=updated_dict,
            receiver_user=receiver_user,
            encargado_role=str(token_payload.get("rol") or "No definido"),
            encargado_name=str(token_payload.get("nombre") or token_payload.get("correo") or "No definido"),
        )
        if not notification_sent:
            print(f"[onboarding/update] En-proceso notification not sent for solicitud_id={solicitud_id}")

    return OnboardingResponse.model_validate(updated_dict)


@router.post("/usuarios/{usuario_id}/estado-onboarding/siguiente")
async def advance_user_onboarding_state(
    usuario_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    requester_id = token_payload.get("sub")
    try:
        requester_id = int(requester_id)
    except Exception:
        raise HTTPException(status_code=400, detail="El token no contiene un id de usuario válido")

    if requester_id != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Solo el usuario titular puede actualizar su estado de onboarding",
        )

    try:
        current = await db.prepare(
            "SELECT id, estado_onboarding FROM USUARIO WHERE id = ? LIMIT 1"
        ).bind(usuario_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo usuario: {str(e)}")

    if not current:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    estado_actual = str(getattr(current, "estado_onboarding", None) or "")
    if estado_actual == "Pendiente":
        estado_siguiente = "En proceso"
    elif estado_actual == "En proceso":
        estado_siguiente = "Finalizado"
    elif estado_actual == "Finalizado":
        raise HTTPException(status_code=400, detail="El estado ya está en su valor final")
    else:
        raise HTTPException(status_code=400, detail=f"Estado actual inválido: {estado_actual}")

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


@router.post("/solicitudes/{solicitud_id}/rechazar", response_model=OnboardingResponse)
async def reject_onboarding_request(
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
    if estado_actual == "Rechazado":
        raise HTTPException(status_code=400, detail="La solicitud ya está rechazada")
    if estado_actual == "Finalizado":
        raise HTTPException(status_code=400, detail="No se puede rechazar una solicitud finalizada")

    try:
        updated = await db.prepare(
            """
            UPDATE SOLICITUDES
            SET estado = ?
            WHERE id = ?
            RETURNING id, id_empleado, fecha_creacion, fecha_fin, estado, especificaciones, destinatario
            """
        ).bind("Rechazado", solicitud_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rechazando solicitud: {str(e)}")

    if not updated:
        raise HTTPException(status_code=500, detail="No fue posible rechazar la solicitud")

    await _register_history(
        db=db,
        id_solicitud=solicitud_id,
        tipo_cambio="CAMBIO_ESTADO",
        valor_anterior=estado_actual,
        valor_nuevo="Rechazado",
    )

    return OnboardingResponse.model_validate(_clean_row_dict(_row_to_dict(updated)))
