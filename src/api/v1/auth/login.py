"""Endpoint de login y obtener usuario actual."""
from fastapi import APIRouter, HTTPException, Request, Header

try:
    from models import LoginRequest, LoginResponse
    from utils import create_access_token, verify_password
except ImportError:
    from ....models import LoginRequest, LoginResponse
    from ....utils import create_access_token, verify_password

from .utils import get_jwt_secret, ACCESS_TOKEN_TTL_SECONDS

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, req: Request):
    """
    Endpoint de login. Valida credenciales contra tabla USUARIO.
    """
    env = req.scope["env"]
    db = env.dataBase

    try:
        result = (
            await db.prepare(
                "SELECT id, correo, contrasena, rol, nombre FROM USUARIO WHERE correo = ? LIMIT 1"
            )
            .bind(payload.correo)
            .first()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error consultando la base de datos: {e}"
        )

    if not result:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not verify_password(payload.contrasena, result.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    jwt_secret = await get_jwt_secret(req)
    access_token = create_access_token(
        {
            "sub": str(result.id),
            "correo": result.correo,
            "rol": result.rol,
            "nombre": result.nombre,
        },
        jwt_secret,
        ACCESS_TOKEN_TTL_SECONDS,
    )

    return {
        "status": "ok",
        "message": "Login exitoso",
        "user": {
            "id": result.id,
            "correo": result.correo,
            "rol": result.rol,
            "nombre": result.nombre,
        },
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
    }


@router.get("/me")
async def get_current_user(req: Request, authorization: str | None = Header(default=None)):
    """
    Obtiene la información del usuario actual basado en el token JWT.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta header Authorization")

    auth_parts = authorization.split(" ", 1)
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato de Authorization inválido")

    token = auth_parts[1]
    jwt_secret = await get_jwt_secret(req)

    try:
        from ...utils import decode_access_token
    except ImportError:
        from .....utils import decode_access_token

    try:
        payload = decode_access_token(token, jwt_secret)
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    env = req.scope["env"]
    db = env.dataBase

    try:
        user = (
            await db.prepare(
                "SELECT id, correo, rol, nombre FROM USUARIO WHERE id = ? LIMIT 1"
            )
            .bind(user_id)
            .first()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando usuario: {e}")

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "status": "ok",
        "user": {
            "id": user.id,
            "correo": user.correo,
            "rol": user.rol,
            "nombre": user.nombre,
        },
    }
