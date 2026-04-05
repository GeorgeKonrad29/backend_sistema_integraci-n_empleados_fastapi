from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _register_history, _row_to_dict

try:
    from models.onboarding import OnboardingResponse, OnboardingUpdateRequest
    from utils import ROLE_CARGO_ACCESS, get_current_token_payload
except ImportError:
    from ....models.onboarding import OnboardingResponse, OnboardingUpdateRequest
    from ....utils import ROLE_CARGO_ACCESS, get_current_token_payload

router = APIRouter()


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

    user_cargo = token_payload.get("cargo")
    if user_cargo is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

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
    destinatario_actual = str(current_dict.get("destinatario") or "").strip().lower()
    rrhh_cargos = set(ROLE_CARGO_ACCESS.get("rrhh", []))

    can_edit = (
        int(user_cargo) in rrhh_cargos
        or (destinatario_actual and destinatario_actual in {nombre_cargo, area})
    )
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
