from fastapi import APIRouter, HTTPException, Request
from ..models import LoginRequest, LoginResponse
from ..utils import hash_password, verify_password

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, req: Request):
    """
    Endpoint de login. Valida credenciales contra la tabla USUARIO.
    Si el usuario tiene contraseña en texto plano, se migra automaticamente a hash.
    
    Args:
        payload: Email y contraseña del usuario
        req: Request object para acceder a la BD via binding dataBase
    
    Returns:
        LoginResponse con datos del usuario autenticado
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

    # Auto-migración: si la contraseña está en texto plano, hashearla
    if not result.contrasena.startswith("pbkdf2_sha256$"):
        try:
            upgraded_hash = hash_password(payload.contrasena)
            await db.prepare("UPDATE USUARIO SET contrasena = ? WHERE id = ?").bind(
                upgraded_hash, result.id
            ).run()
        except Exception:
            pass

    return {
        "status": "ok",
        "message": "Login exitoso",
        "user": {
            "id": result.id,
            "correo": result.correo,
            "rol": result.rol,
            "nombre": result.nombre,
        },
    }
