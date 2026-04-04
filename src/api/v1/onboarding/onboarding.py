from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, Security

try:
    from models.onboarding import (
        EstadoSolicitud,
        OnboardingHistoryResponse,
        OnboardingRequest,
        OnboardingResponse,
        OnboardingUpdateRequest,
    )
    from utils import ROLE_CARGO_ACCESS, get_current_token_payload, require_permission
except ImportError:
    from ....models.onboarding import (
        EstadoSolicitud,
        OnboardingHistoryResponse,
        OnboardingRequest,
        OnboardingResponse,
        OnboardingUpdateRequest,
    )
    from ....utils import ROLE_CARGO_ACCESS, get_current_token_payload, require_permission

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


def _rows_to_history_response_list(rows) -> list[dict]:
    final_list = []
    for row in rows:
        final_list.append(_clean_row_dict(_row_to_dict(row)))
    return final_list


async def _register_history(
    db,
    id_solicitud: int,
    tipo_cambio: str,
    valor_anterior: str | None,
    valor_nuevo: str | None,
):
    await db.prepare(
        """
        INSERT INTO HISTORIAL (
            id_solicitud,
            fecha_cambio,
            tipo_cambio,
            estado_antiguo,
            nuevo_estado
        ) VALUES (?, datetime('now'), ?, ?, ?)
        """
    ).bind(id_solicitud, tipo_cambio, valor_anterior, valor_nuevo).run()


async def _get_next_responsible_destination(db, cargo_id: int) -> tuple[str | None, str | None] | None:
    try:
        next_cargo = await db.prepare(
            """
            SELECT nombre_cargo, area
            FROM JERARQUIA
            WHERE id_jefe_inmediato = ?
            ORDER BY id
            LIMIT 1
            """
        ).bind(cargo_id).first()
    except Exception:
        return None

    if not next_cargo:
        return None

    return (
        str(next_cargo.nombre_cargo or "").strip() or None,
        str(next_cargo.area or "").strip() or None,
    )


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

        await _register_history(
            db=db,
            id_solicitud=int(result.id),
            tipo_cambio="CREACION",
            valor_anterior=None,
            valor_nuevo=str(result.estado),
        )

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
    estado: str | None = Query(default=None),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
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

    valid_states = {"Pendiente", "En proceso", "Finalizado"}
    if estado is not None and estado not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Use uno de: {sorted(valid_states)}",
        )

    def _validate_iso_datetime(value: str | None, field_name: str) -> str | None:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value).isoformat()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} debe tener formato ISO-8601 (ej: 2026-04-01T00:00:00)",
            )

    fecha_desde_iso = _validate_iso_datetime(fecha_desde, "fecha_desde")
    fecha_hasta_iso = _validate_iso_datetime(fecha_hasta, "fecha_hasta")

    if fecha_desde_iso and fecha_hasta_iso and fecha_desde_iso > fecha_hasta_iso:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    where_clauses = ["j.id_jefe_inmediato = ?"]
    bindings: list[str | int] = [cargo_jefe]

    if estado is not None:
        where_clauses.append("s.estado = ?")
        bindings.append(estado)

    if fecha_desde_iso is not None:
        where_clauses.append("s.fecha_creacion >= ?")
        bindings.append(fecha_desde_iso)

    if fecha_hasta_iso is not None:
        where_clauses.append("s.fecha_creacion <= ?")
        bindings.append(fecha_hasta_iso)

    try:
        query_result = await db.prepare(
            f"""
            SELECT s.id, s.id_empleado, s.fecha_creacion, s.fecha_fin, s.estado, s.especificaciones, s.destinatario
            FROM SOLICITUDES s
            JOIN USUARIO u ON u.id = s.id_empleado
            JOIN JERARQUIA j ON j.id = u.cargo
            WHERE {" AND ".join(where_clauses)}
            ORDER BY s.fecha_creacion DESC
            """
        ).bind(*bindings).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener solicitudes del equipo: {str(e)}")

    return _rows_to_onboarding_response_list(query_result.results)


@router.patch("/{solicitud_id}", response_model=OnboardingResponse)
async def update_onboarding_request(
    solicitud_id: int,
    payload: OnboardingUpdateRequest,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Actualiza una solicitud de onboarding y registra cada cambio en HISTORIAL.
    """
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

    # Cuando el jefe inmediato la pone "En proceso", se traslada automáticamente
    # al siguiente responsable para que aparezca en su bandeja.
    if (
        int(user_cargo) not in rrhh_cargos
        and payload.estado is not None
        and payload.estado == EstadoSolicitud.EN_PROCESO
        and "destinatario" not in payload_data
    ):
        next_responsible = await _get_next_responsible_destination(db, int(user_cargo))
        if next_responsible:
            next_destinatario = next_responsible[0] or next_responsible[1] or next_destinatario

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


@router.get("/solicitudes/{solicitud_id}/historial", response_model=list[OnboardingHistoryResponse])
async def get_onboarding_request_history(
    solicitud_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Devuelve la trazabilidad de una solicitud de onboarding.
    Acceso: RRHH, jefe inmediato del empleado de la solicitud, o destinatario actual.
    """
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


@router.get("/solicitudes-asignadas", response_model=list[OnboardingResponse])
async def list_assigned_onboarding_requests(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
    estado: str | None = Query(default=None),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
):
    """
    Lista las solicitudes de onboarding asignadas al usuario logueado para resolver,
    comparando el destinatario con su nombre de cargo o su área.
    """
    env = req.scope["env"]
    db = env.dataBase

    cargo_id = token_payload.get("cargo")
    if cargo_id is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    try:
        cargo_info = await db.prepare(
            "SELECT nombre_cargo, area FROM JERARQUIA WHERE id = ? LIMIT 1"
        ).bind(cargo_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo cargo del usuario: {str(e)}")

    if not cargo_info:
        raise HTTPException(status_code=404, detail="No se encontró el cargo del usuario en jerarquía")

    nombre_cargo = str(cargo_info.nombre_cargo or "").strip()
    area = str(cargo_info.area or "").strip()

    if not nombre_cargo and not area:
        return []

    valid_states = {"Pendiente", "En proceso", "Finalizado"}
    if estado is not None and estado not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Use uno de: {sorted(valid_states)}",
        )

    def _validate_iso_datetime(value: str | None, field_name: str) -> str | None:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value).isoformat()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} debe tener formato ISO-8601 (ej: 2026-04-01T00:00:00)",
            )

    fecha_desde_iso = _validate_iso_datetime(fecha_desde, "fecha_desde")
    fecha_hasta_iso = _validate_iso_datetime(fecha_hasta, "fecha_hasta")

    if fecha_desde_iso and fecha_hasta_iso and fecha_desde_iso > fecha_hasta_iso:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    where_clauses = [
        "(LOWER(TRIM(s.destinatario)) = LOWER(TRIM(?)) OR LOWER(TRIM(s.destinatario)) = LOWER(TRIM(?)))"
    ]
    bindings: list[str] = [nombre_cargo, area]

    if estado is not None:
        where_clauses.append("s.estado = ?")
        bindings.append(estado)

    if fecha_desde_iso is not None:
        where_clauses.append("s.fecha_creacion >= ?")
        bindings.append(fecha_desde_iso)

    if fecha_hasta_iso is not None:
        where_clauses.append("s.fecha_creacion <= ?")
        bindings.append(fecha_hasta_iso)

    query = f"""
        SELECT s.id, s.id_empleado, s.fecha_creacion, s.fecha_fin, s.estado, s.especificaciones, s.destinatario
        FROM SOLICITUDES s
        WHERE {' AND '.join(where_clauses)}
        ORDER BY s.fecha_creacion DESC
    """

    try:
        query_result = await db.prepare(query).bind(*bindings).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo solicitudes asignadas: {str(e)}")

    return _rows_to_onboarding_response_list(query_result.results)