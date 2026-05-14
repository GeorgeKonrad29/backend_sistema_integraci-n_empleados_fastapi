from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from utils.jwt import decode_access_token
except ImportError:
    from .jwt import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

# Mapa editable: cada "rol funcional" define qué IDs de cargo están permitidos.
# Agrega aquí nuevos roles y sus cargos.
ROLE_CARGO_ACCESS: dict[str, list[int]] = {
    "rrhh": [1, 48, 49],
    "servicios_generales": [4],
    "inventario": [],
}

# Mapa editable: cada permiso (acción/ruta) define qué roles funcionales pueden acceder.
# Agrega o ajusta permisos según crezca el sistema.
PERMISSION_ROLES: dict[str, list[str]] = {
    "usuarios.crear": ["rrhh"],
    "usuarios.eliminar": ["rrhh"],
    "auth.signup": ["rrhh"],
    "onboarding.crear": ["rrhh"],
    "onboarding.listar": ["rrhh"],
    "onboarding.dotacion.crear": ["rrhh"],
    "onboarding.dotacion.listar": ["rrhh"],
    "onboarding.estadisticas": ["rrhh"],
    "puestos.asignar": ["servicios_generales"],
    "cargos.listar": ["rrhh", "inventario"],
}


def get_payload_cargo(payload: dict) -> int:
    cargo = payload.get("cargo")
    if cargo is None:
        raise HTTPException(status_code=400, detail="El token no contiene el cargo del usuario")
    return int(cargo)


def is_rrhh_cargo(cargo_id: int) -> bool:
    return int(cargo_id) in set(ROLE_CARGO_ACCESS.get("rrhh", []))


async def has_direct_reports(db, cargo_id: int) -> bool:
    row = await db.prepare(
        "SELECT id FROM JERARQUIA WHERE id_jefe_inmediato = ? LIMIT 1"
    ).bind(cargo_id).first()
    return bool(row)


async def get_cargo_name_area(db, cargo_id: int) -> tuple[str, str] | None:
    row = await db.prepare(
        "SELECT nombre_cargo, area FROM JERARQUIA WHERE id = ? LIMIT 1"
    ).bind(cargo_id).first()
    if not row:
        return None
    return (str(row.nombre_cargo or "").strip(), str(row.area or "").strip())


async def is_direct_boss_of_cargo(db, boss_cargo_id: int, employee_cargo_id: int) -> bool:
    row = await db.prepare(
        "SELECT id_jefe_inmediato FROM JERARQUIA WHERE id = ? LIMIT 1"
    ).bind(employee_cargo_id).first()
    if not row:
        return False
    return getattr(row, "id_jefe_inmediato", None) == int(boss_cargo_id)


async def destination_matches_user_cargo(db, cargo_id: int, destinatario: str | None) -> bool:
    if not destinatario:
        return False
    cargo_info = await get_cargo_name_area(db, int(cargo_id))
    if not cargo_info:
        return False
    nombre_cargo, area = cargo_info
    target = str(destinatario).strip().lower()
    return bool(target and target in {nombre_cargo.lower(), area.lower()})


async def can_create_onboarding_for_employee(db, creator_cargo_id: int, employee_cargo_id: int | None) -> bool:
    if is_rrhh_cargo(creator_cargo_id):
        return True
    if employee_cargo_id is None:
        return False
    return await is_direct_boss_of_cargo(db, creator_cargo_id, int(employee_cargo_id))


async def can_manage_dotacion(db, user_cargo_id: int) -> bool:
    if is_rrhh_cargo(user_cargo_id):
        return True
    return await has_direct_reports(db, user_cargo_id)


async def can_update_onboarding_request(db, user_cargo_id: int, destinatario: str | None) -> bool:
    if is_rrhh_cargo(user_cargo_id):
        return True
    return await destination_matches_user_cargo(db, user_cargo_id, destinatario)


async def can_delete_onboarding_request(db, user_cargo_id: int, employee_cargo_id: int | None) -> bool:
    if is_rrhh_cargo(user_cargo_id):
        return True
    if employee_cargo_id is None:
        return False
    return await is_direct_boss_of_cargo(db, user_cargo_id, int(employee_cargo_id))


async def can_view_onboarding_history(
    db,
    user_cargo_id: int,
    destinatario: str | None,
    employee_cargo_id: int | None,
) -> bool:
    if is_rrhh_cargo(user_cargo_id):
        return True
    if await destination_matches_user_cargo(db, user_cargo_id, destinatario):
        return True
    if employee_cargo_id is not None and await is_direct_boss_of_cargo(db, user_cargo_id, int(employee_cargo_id)):
        return True
    return False


async def get_jwt_secret(req: Request) -> str:
    env = req.scope["env"]

    # Intentar con JWTSecret binding
    secret_binding = getattr(env, "JWTSecret", None)
    if secret_binding and hasattr(secret_binding, "get"):
        fetched_secret = await secret_binding.get()
        if fetched_secret and str(fetched_secret).strip():
            return str(fetched_secret)

    # Intentar con JWT_SECRET variable
    jwt_secret = getattr(env, "JWT_SECRET", None)
    if isinstance(jwt_secret, str) and jwt_secret.strip():
        return jwt_secret

    # Intentar con jwt_secret binding
    secret_binding = getattr(env, "jwt_secret", None)
    if secret_binding and hasattr(secret_binding, "get"):
        fetched_secret = await secret_binding.get()
        if fetched_secret and str(fetched_secret).strip():
            return str(fetched_secret)

    raise HTTPException(
        status_code=500,
        detail="JWT secret no configurado (buscó: JWTSecret, JWT_SECRET, jwt_secret).",
    )


async def get_current_token_payload(
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Credenciales no proporcionadas")

    jwt_secret = await get_jwt_secret(req)

    try:
        return decode_access_token(credentials.credentials, jwt_secret)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def _allowed_cargos_for_permission(permission_key: str) -> list[int]:
    roles = PERMISSION_ROLES.get(permission_key)
    if not roles:
        return []

    allowed: set[int] = set()
    for role_name in roles:
        for cargo_id in ROLE_CARGO_ACCESS.get(role_name, []):
            allowed.add(cargo_id)

    return sorted(allowed)


def require_permission(permission_key: str):
    async def _dependency(
        req: Request,
        credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    ) -> dict:
        payload = await get_current_token_payload(req, credentials)
        cargo = payload.get("cargo")

        allowed_cargos = _allowed_cargos_for_permission(permission_key)
        if not allowed_cargos:
            raise HTTPException(
                status_code=500,
                detail=f"Permiso '{permission_key}' sin configuración en ROLE_CARGO_ACCESS/PERMISSION_ROLES.",
            )

        if cargo not in allowed_cargos:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"No tiene permisos para '{permission_key}'. "
                    f"Cargos permitidos: {allowed_cargos}."
                ),
            )

        return payload

    return _dependency
