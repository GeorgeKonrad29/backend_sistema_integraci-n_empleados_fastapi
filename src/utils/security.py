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
    "rrhh": [1, 7, 24],
    "inventario": [],
}

# Mapa editable: cada permiso (acción/ruta) define qué roles funcionales pueden acceder.
# Agrega o ajusta permisos según crezca el sistema.
PERMISSION_ROLES: dict[str, list[str]] = {
    "usuarios.crear": ["rrhh"],
    "onboarding.crear": ["rrhh"],
    "onboarding.listar": ["rrhh"],
    "cargos.listar": ["rrhh", "inventario"],
}


async def get_jwt_secret(req: Request) -> str:
    env = req.scope["env"]

    jwt_secret = getattr(env, "JWT_SECRET", None)
    if isinstance(jwt_secret, str) and jwt_secret.strip():
        return jwt_secret

    secret_binding = getattr(env, "jwt_secret", None)
    if secret_binding and hasattr(secret_binding, "get"):
        fetched_secret = await secret_binding.get()
        if fetched_secret and str(fetched_secret).strip():
            return str(fetched_secret)

    raise HTTPException(
        status_code=500,
        detail="JWT secret no configurado en el entorno (JWT_SECRET o binding jwt_secret).",
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
