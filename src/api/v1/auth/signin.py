"""Endpoints de registro (signup) y activación de contraseña."""
import secrets
import time
from fastapi import APIRouter, HTTPException, Request, Security
from fastapi.responses import HTMLResponse

try:
    from models import (
        ActivatePasswordRequest,
        ActivatePasswordResponse,
        SignupRequest,
        SignupResponse,
    )
    from utils import hash_password
    from ....utils import require_permission
    from api.v1.pendiente_a_eliminar import get_activation_form_html
except ImportError:
    from ....models import (
        ActivatePasswordRequest,
        ActivatePasswordResponse,
        SignupRequest,
        SignupResponse,
    )
    from ....utils import hash_password, require_permission
    from ..pendiente_a_eliminar import get_activation_form_html

from .utils import (
    ensure_activation_table,
    send_activation_email,
    ACTIVATION_TOKEN_TTL_SECONDS,
)

router = APIRouter()


@router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupRequest, req: Request,token_payload: dict = Security(require_permission("auth.registrar"))):
    """
    Endpoint de registro. Crea usuario pendiente y genera enlace de activación.
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
        ).bind(
            payload.correo, placeholder_password, payload.nombre, payload.rol or "Operador", payload.cargo
        ).first()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario: {e}",
        )

    if not created_user:
        raise HTTPException(status_code=500, detail="No se pudo crear el usuario")

    now_ts = int(time.time())
    expires_at = now_ts + ACTIVATION_TOKEN_TTL_SECONDS
    token = secrets.token_urlsafe(32)

    try:
        await db.prepare(
            "INSERT OR REPLACE INTO ACTIVACION_USUARIO (user_id, token, expires_at, used, created_at) VALUES (?, ?, ?, 0, ?)"
        ).bind(created_user.id, token, expires_at, now_ts).run()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando token de activación: {e}",
        )

    activation_link = f"{req.base_url}v1/auth/activate-password?token={token}"
    email_sent = await send_activation_email(
        payload.correo, payload.nombre, activation_link, req
    )
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
        },
        "activation_link": activation_link,
        "email_sent": email_sent,
    }


@router.get("/activate-password", response_class=HTMLResponse)
async def activate_password_form(token: str = ""):
    """
    Muestra formulario HTML para activar contraseña.
    """
    return get_activation_form_html(token)


@router.post("/activate-password", response_model=ActivatePasswordResponse)
async def activate_password(payload: ActivatePasswordRequest, req: Request):
    """
    Define la contraseña final usando el token generado en signup.
    """
    env = req.scope["env"]
    db = env.dataBase

    await ensure_activation_table(db)

    now_ts = int(time.time())

    try:
        activation = (
            await db.prepare(
                "SELECT user_id, expires_at, used FROM ACTIVACION_USUARIO WHERE token = ? LIMIT 1"
            )
            .bind(payload.token)
            .first()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando token: {e}")

    if not activation:
        raise HTTPException(status_code=400, detail="Token inválido")

    if int(activation.used) == 1:
        raise HTTPException(status_code=400, detail="Token ya utilizado")

    if int(activation.expires_at) < now_ts:
        raise HTTPException(status_code=400, detail="Token expirado")

    password_hash = hash_password(payload.contrasena)

    try:
        await db.prepare("UPDATE USUARIO SET contrasena = ? WHERE id = ?").bind(
            password_hash, activation.user_id
        ).run()
        await db.prepare("UPDATE ACTIVACION_USUARIO SET used = 1 WHERE token = ?").bind(
            payload.token
        ).run()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activando usuario: {e}")

    return {"status": "ok", "message": "Contraseña activada correctamente"}
