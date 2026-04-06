"""Endpoint de login y obtener usuario actual."""
from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models import LoginRequest, LoginResponse
    from utils import create_access_token, get_current_token_payload, verify_password
except ImportError:
    from ....models import LoginRequest, LoginResponse
    from ....utils import create_access_token, get_current_token_payload, verify_password

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
                "SELECT id, correo, contrasena, rol, nombre, cargo FROM USUARIO WHERE correo = ? LIMIT 1"
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
            "cargo": result.cargo,
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
            "cargo": result.cargo,
        },
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
    }


@router.get("/me")
async def get_current_user(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Obtiene la información del usuario actual basado en el token JWT.
    """
    user_id = int(token_payload.get("sub", 0))

    env = req.scope["env"]
    db = env.dataBase

    try:
        user = (
            await db.prepare(
                "SELECT id, correo, rol, nombre, cargo FROM USUARIO WHERE id = ? LIMIT 1"
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
            "cargo": user.cargo,
        },
    }


@router.post("/logout")
async def logout(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Cierre de sesión lógico para cliente frontend.
    En JWT stateless el cliente debe descartar el token.
    """
    return {
        "status": "ok",
        "message": "Logout exitoso",
    }
