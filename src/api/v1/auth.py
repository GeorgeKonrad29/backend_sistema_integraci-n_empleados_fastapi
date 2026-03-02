from fastapi import APIRouter, HTTPException, Request

try:
    from models import LoginRequest, LoginResponse
    from utils import hash_password, verify_password
except ImportError:
    from ...models import LoginRequest, LoginResponse
    from ...utils import hash_password, verify_password

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, req: Request):
    env = req.scope["env"]
    db = env.dataBase
    password_pepper = getattr(env, "PASSWORD_PEPPER", None)

    if not password_pepper:
        raise HTTPException(
            status_code=500,
            detail="Secret PASSWORD_PEPPER no está configurado en Cloudflare",
        )

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

    if not verify_password(payload.contrasena, result.contrasena, password_pepper):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not result.contrasena.startswith("pbkdf2_sha256_peppered$"):
        try:
            upgraded_hash = hash_password(payload.contrasena, password_pepper)
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
