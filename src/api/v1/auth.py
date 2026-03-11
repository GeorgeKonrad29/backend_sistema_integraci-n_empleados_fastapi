from fastapi import APIRouter, HTTPException, Request, Security
from fastapi.responses import HTMLResponse
import secrets
import time

try:
    from models import (
        ActivatePasswordRequest,
        ActivatePasswordResponse,
        JerarquiaResponse,
        LoginRequest,
        LoginResponse,
        SignupRequest,
        SignupResponse,
    )
    from utils import (
        get_current_token_payload,
        get_jwt_secret,
        create_access_token,
        require_permission,
        verify_password,
    )
    from api.v1.pendiente_a_eliminar import get_activation_form_html
    from api.v1.auth_activation import (
        ACTIVATION_TOKEN_TTL_SECONDS,
        activate_password_with_token,
        ensure_activation_table,
        send_activation_email,
    )
except ImportError:
    from ...models import (
        ActivatePasswordRequest,
        ActivatePasswordResponse,
        JerarquiaResponse,
        LoginRequest,
        LoginResponse,
        SignupRequest,
        SignupResponse,
    )
    from ...utils import (
        get_current_token_payload,
        get_jwt_secret,
        create_access_token,
        require_permission,
        verify_password,
    )
    from .pendiente_a_eliminar import get_activation_form_html
    from .auth_activation import (
        ACTIVATION_TOKEN_TTL_SECONDS,
        activate_password_with_token,
        ensure_activation_table,
        send_activation_email,
    )

router = APIRouter()

ACCESS_TOKEN_TTL_SECONDS = 3600



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
async def get_current_user(req: Request, token_payload: dict = Security(get_current_token_payload)):
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


@router.post("/signup", response_model=SignupResponse)
async def signup(
    payload: SignupRequest,
    req: Request,
    token_payload: dict = Security(require_permission("usuarios.crear")),
):
    """
    Endpoint de registro. Protegido. Solo usuarios con cargo 1, 7 o 24 pueden crear otros usuarios.
    """
    env = req.scope["env"]
    db = env.dataBase

    await ensure_activation_table(db)

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

    placeholder_password = "PENDIENTE_ACTIVACION"

    try:
        created_user = await db.prepare(
            "INSERT INTO USUARIO (correo, contrasena, nombre, rol, cargo) VALUES (?, ?, ?, ?, ?) RETURNING id, cargo"
        ).bind(payload.correo, placeholder_password, payload.nombre, payload.rol or "Operador", payload.cargo).first()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario: {e}",
        )

    if not created_user:
        raise HTTPException(status_code=500, detail="No se pudo crear el usuario")

    now_ts = int(time.time())
    expires_at = now_ts + ACTIVATION_TOKEN_TTL_SECONDS
    token_activation = secrets.token_urlsafe(32)

    try:
        await db.prepare(
            "INSERT OR REPLACE INTO ACTIVACION_USUARIO (user_id, token, expires_at, used, created_at) VALUES (?, ?, ?, 0, ?)"
        ).bind(created_user.id, token_activation, expires_at, now_ts).run()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando token de activación: {e}",
        )

    activation_link = f"{req.base_url}v1/auth/activate-password?token={token_activation}"
    email_sent = await send_activation_email(payload.correo, payload.nombre, activation_link, req)
    response_message = "Usuario creado. Revisa tu correo para activar la cuenta."
    if not email_sent:
        response_message = "Usuario creado. Correo no enviado, usa activation_link."

    return {
        "status": "ok",
        "message": response_message,
        "user": {
            "id": created_user.id,
            "correo": payload.correo,
            "rol": payload.rol,
            "nombre": payload.nombre,
            "cargo": created_user.cargo,
        },
        "activation_link": activation_link,
        "email_sent": email_sent,
    }


@router.get("/cargos", response_model=list[JerarquiaResponse])
async def get_cargos(req: Request, token_payload: dict = Security(require_permission("cargos.listar"))):
    """
    Endpoint protegido que devuelve todos los cargos/jerarquía.
    Requiere JWT válido.
    """
    env = req.scope["env"]
    db = env.dataBase

    try:
        cargos = await db.prepare(
            "SELECT id, nombre_cargo, area, id_jefe_inmediato FROM JERARQUIA ORDER BY id"
        ).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando cargos: {e}")

    result_list = []
    for cargo_row in cargos.results:
        try:
            cargo_dict = {
                "id": cargo_row.id,
                "nombre_cargo": cargo_row.nombre_cargo,
                "area": cargo_row.area,
                "id_jefe_inmediato": cargo_row.id_jefe_inmediato,
            }
            result_list.append(cargo_dict)
        except Exception:
            pass

    return result_list


@router.get("/activate-password", response_class=HTMLResponse)
async def activate_password_form(token: str = ""):
    return get_activation_form_html(token)


@router.post("/activate-password", response_model=ActivatePasswordResponse)
async def activate_password(payload: ActivatePasswordRequest, req: Request):
    """
    Define la contraseña final usando el token generado en signup.
    """
    return await activate_password_with_token(payload.token, payload.contrasena, req)

