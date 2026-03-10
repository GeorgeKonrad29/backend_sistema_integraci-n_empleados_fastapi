from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from utils import decode_access_token
except ImportError:
    from .jwt import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)
ALLOWED_CARGOS = [1, 7, 24]


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


async def require_admin_cargo(
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    payload = await get_current_token_payload(req, credentials)
    cargo = payload.get("cargo")

    if cargo not in ALLOWED_CARGOS:
        raise HTTPException(
            status_code=403,
            detail=f"No tiene permisos. Solo usuarios con cargo {ALLOWED_CARGOS} pueden acceder.",
        )

    return payload
