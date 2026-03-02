from fastapi import APIRouter, HTTPException, Request

try:
    from models import LoginRequest, LoginResponse, SignupRequest, SignupResponse
    from utils import hash_password, verify_password
except ImportError:
    from ...models import LoginRequest, LoginResponse, SignupRequest, SignupResponse
    from ...utils import hash_password, verify_password

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


@router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupRequest, req: Request):
    """
    Endpoint de registro. Crea un nuevo usuario con contraseña hasheada.
    """
    env = req.scope["env"]
    db = env.dataBase

    # Validar que el email no exista
    try:
        existing = (
            await db.prepare("SELECT id FROM USUARIO WHERE correo = ? LIMIT 1")
            .bind(payload.correo)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="El email ya está registrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error consultando la base de datos: {e}"
        )

    # Hash la contraseña
    password_hash = hash_password(payload.contrasena)

    # Insertar usuario
    try:
        result = await db.prepare(
            "INSERT INTO USUARIO (correo, contrasena, nombre, rol) VALUES (?, ?, ?, ?) RETURNING id"
        ).bind(payload.correo, password_hash, payload.nombre, payload.rol or 0).first()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario: {e}",
        )

    if not result:
        raise HTTPException(
            status_code=500, detail="No se pudo crear el usuario"
        )

    return {
        "status": "ok",
        "message": "Usuario registrado exitosamente",
        "user": {
            "id": result.id,
            "correo": payload.correo,
            "rol": payload.rol,
            "nombre": payload.nombre,
        },
    }

