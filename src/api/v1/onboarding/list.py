from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, Security

from .common import _rows_to_onboarding_response_list

try:
    from models.onboarding import OnboardingResponse
    from models.auth import TeamEmployee
    from utils import get_current_token_payload, require_permission
except ImportError:
    from ....models.onboarding import OnboardingResponse
    from ....models.auth import TeamEmployee
    from ....utils import get_current_token_payload, require_permission

router = APIRouter()


@router.get("/", response_model=list[OnboardingResponse])
async def list_onboarding_requests(
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.listar")),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        # Por defecto no mostrar solicitudes marcadas como 'Eliminada'
        query_result = await db.prepare("SELECT * FROM SOLICITUDES WHERE estado != 'Eliminada' ORDER BY fecha_creacion DESC").all()
        return _rows_to_onboarding_response_list(query_result.results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener solicitudes: {str(e)}")


@router.get("/mis-solicitudes", response_model=list[OnboardingResponse])
async def list_my_onboarding_requests(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
    estado: str | None = Query(default=None),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
):
    env = req.scope["env"]
    db = env.dataBase

    user_id = token_payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=400, detail="El token no contiene el id del usuario")

    try:
        user_id = int(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="El id de usuario en el token no es válido")

    valid_states = {"Pendiente", "En proceso", "Finalizado", "Rechazado"}
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

    where_clauses = ["id_empleado = ?"]
    bindings: list[str | int] = [user_id]

    if estado is not None:
        where_clauses.append("estado = ?")
        bindings.append(estado)
    else:
        # Excluir solicitudes eliminadas por defecto
        where_clauses.append("estado != 'Eliminada'")

    if fecha_desde_iso is not None:
        where_clauses.append("fecha_creacion >= ?")
        bindings.append(fecha_desde_iso)

    if fecha_hasta_iso is not None:
        where_clauses.append("fecha_creacion <= ?")
        bindings.append(fecha_hasta_iso)

    query = f"""
        SELECT id, id_empleado, fecha_creacion, fecha_fin, estado, especificaciones, destinatario
        FROM SOLICITUDES
        WHERE {' AND '.join(where_clauses)}
        ORDER BY fecha_creacion DESC
    """

    try:
        query_result = await db.prepare(query).bind(*bindings).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo sus solicitudes: {str(e)}")

    return _rows_to_onboarding_response_list(query_result.results)


@router.get("/solicitudes-equipo", response_model=list[OnboardingResponse])
async def list_team_onboarding_requests(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
    estado: str | None = Query(default=None),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
):
    env = req.scope["env"]
    db = env.dataBase

    cargo_jefe = token_payload.get("cargo")
    if cargo_jefe is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    valid_states = {"Pendiente", "En proceso", "Finalizado", "Rechazado"}
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
    else:
        where_clauses.append("s.estado != 'Eliminada'")

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
            WHERE {' AND '.join(where_clauses)}
            ORDER BY s.fecha_creacion DESC
            """
        ).bind(*bindings).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener solicitudes del equipo: {str(e)}")

    return _rows_to_onboarding_response_list(query_result.results)


@router.get("/mi-equipo/empleados-no-finalizados", response_model=list[TeamEmployee])
async def list_my_team_employees_pending_onboarding(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
    estado: str | None = Query(default=None),
):
    env = req.scope["env"]
    db = env.dataBase

    cargo_jefe = token_payload.get("cargo")
    if cargo_jefe is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    valid_states = {"Pendiente", "En proceso", "Finalizado", "Rechazado"}
    if estado is not None and estado not in valid_states:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Use uno de: {sorted(valid_states)}")

    try:
        if estado is None:
            query = '''
            SELECT u.id, u.nombre, u.correo, u.cargo, u.estado_onboarding, j.nombre_cargo, j.area
            FROM USUARIO u
            JOIN JERARQUIA j ON j.id = u.cargo
            WHERE j.id_jefe_inmediato = ? AND (u.estado_onboarding IS NULL OR u.estado_onboarding != 'Finalizado')
            ORDER BY u.nombre
            '''
            query_result = await db.prepare(query).bind(int(cargo_jefe)).all()
        else:
            query = '''
            SELECT u.id, u.nombre, u.correo, u.cargo, u.estado_onboarding, j.nombre_cargo, j.area
            FROM USUARIO u
            JOIN JERARQUIA j ON j.id = u.cargo
            WHERE j.id_jefe_inmediato = ? AND u.estado_onboarding = ?
            ORDER BY u.nombre
            '''
            query_result = await db.prepare(query).bind(int(cargo_jefe), estado).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo empleados del equipo: {str(e)}")

    employees: list[dict] = []
    for row in query_result.results:
        employees.append(
            {
                "id": getattr(row, "id", None),
                "nombre": getattr(row, "nombre", None),
                "correo": getattr(row, "correo", None),
                "cargo": getattr(row, "cargo", None),
                "estado_onboarding": getattr(row, "estado_onboarding", None),
                "nombre_cargo": getattr(row, "nombre_cargo", None),
                "area": getattr(row, "area", None),
            }
        )

    return employees


@router.get("/mi-equipo/empleados", response_model=list[TeamEmployee])
async def list_my_team_employees_all(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
    estado: str | None = Query(default=None),
):
    """
    Devuelve todos los usuarios que están a cargo del empleado logueado (informes directos).
    - Si `estado` es proporcionado, filtra por `estado_onboarding`.
    - Por defecto excluye usuarios marcados como 'Eliminada'.
    """
    env = req.scope["env"]
    db = env.dataBase

    cargo_jefe = token_payload.get("cargo")
    if cargo_jefe is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")

    valid_states = {"Pendiente", "En proceso", "Finalizado", "Rechazado"}
    if estado is not None and estado not in valid_states:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Use uno de: {sorted(valid_states)}")

    try:
        if estado is None:
            query = '''
            SELECT u.id, u.nombre, u.correo, u.cargo, u.estado_onboarding, j.nombre_cargo, j.area
            FROM USUARIO u
            JOIN JERARQUIA j ON j.id = u.cargo
            WHERE j.id_jefe_inmediato = ? AND (u.estado_onboarding IS NULL OR u.estado_onboarding != 'Eliminada')
            ORDER BY u.nombre
            '''
            query_result = await db.prepare(query).bind(int(cargo_jefe)).all()
        else:
            query = '''
            SELECT u.id, u.nombre, u.correo, u.cargo, u.estado_onboarding, j.nombre_cargo, j.area
            FROM USUARIO u
            JOIN JERARQUIA j ON j.id = u.cargo
            WHERE j.id_jefe_inmediato = ? AND u.estado_onboarding = ?
            ORDER BY u.nombre
            '''
            query_result = await db.prepare(query).bind(int(cargo_jefe), estado).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo empleados del equipo: {str(e)}")

    employees: list[dict] = []
    for row in query_result.results:
        employees.append(
            {
                "id": getattr(row, "id", None),
                "nombre": getattr(row, "nombre", None),
                "correo": getattr(row, "correo", None),
                "cargo": getattr(row, "cargo", None),
                "estado_onboarding": getattr(row, "estado_onboarding", None),
                "nombre_cargo": getattr(row, "nombre_cargo", None),
                "area": getattr(row, "area", None),
            }
        )

    return employees


@router.get("/solicitudes-asignadas", response_model=list[OnboardingResponse])
async def list_assigned_onboarding_requests(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
    estado: str | None = Query(default=None),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
):
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

    valid_states = {"En proceso"}
    if estado is not None and estado not in valid_states:
        raise HTTPException(
            status_code=400,
            detail="En solicitudes asignadas solo se permite estado='En proceso'",
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
        "(LOWER(TRIM(s.destinatario)) = LOWER(TRIM(?)) OR LOWER(TRIM(s.destinatario)) = LOWER(TRIM(?)))",
        "s.estado = ?",
    ]
    bindings: list[str] = [nombre_cargo, area, "En proceso"]

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
