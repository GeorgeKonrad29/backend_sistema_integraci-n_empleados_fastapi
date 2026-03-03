from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
import json
import secrets
import time

try:
    from utils.resend import fetch as fetch_resend_api_key
except ImportError:
    from ...utils.resend import fetch as fetch_resend_api_key

try:
    from models import (
        ActivatePasswordRequest,
        ActivatePasswordResponse,
        LoginRequest,
        LoginResponse,
        SignupRequest,
        SignupResponse,
    )
    from utils import hash_password, verify_password
    from api.v1.pendiente_a_eliminar import get_activation_form_html
except ImportError:
    from ...models import (
        ActivatePasswordRequest,
        ActivatePasswordResponse,
        LoginRequest,
        LoginResponse,
        SignupRequest,
        SignupResponse,
    )
    from ...utils import hash_password, verify_password
    from .pendiente_a_eliminar import get_activation_form_html

router = APIRouter()

ACTIVATION_TOKEN_TTL_SECONDS = 3600
RESEND_FROM_EMAIL = "onboarding@resend.dev"


async def ensure_activation_table(db):
    await db.prepare(
        """
        CREATE TABLE IF NOT EXISTS ACTIVACION_USUARIO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            token TEXT NOT NULL UNIQUE,
            expires_at INTEGER NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES USUARIO(id)
        )
        """
    ).run()


async def send_activation_email(to_email: str, user_name: str, activation_link: str, req: Request) -> bool:
    # Get API key from Cloudflare Secrets
    try:
        env = req.scope["env"]
        resend_api_key = await fetch_resend_api_key(req, env)
    except Exception:
        return False
    
    if not resend_api_key or not RESEND_FROM_EMAIL:
        return False

    try:
        from pyodide.http import pyfetch
    except Exception:
        return False

    email_payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": "Activa tu cuenta",
        "html": (
            f"<p>Hola {user_name},</p>"
            "<p>Tu cuenta fue creada correctamente.</p>"
            f"<p>Activa tu contraseña aquí: <a href=\"{activation_link}\">Activar cuenta</a></p>"
            "<p>Este enlace expira en 1 hora.</p>"
        ),
    }

    try:
        response = await pyfetch(
            "https://api.resend.com/emails",
            method="POST",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            body=json.dumps(email_payload),
        )
        return response.status in [200, 201, 202]
    except Exception:
        return False


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
            "INSERT INTO USUARIO (correo, contrasena, nombre, rol) VALUES (?, ?, ?, ?) RETURNING id"
        ).bind(payload.correo, placeholder_password, payload.nombre, payload.rol or 0).first()
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
        },
        "activation_link": activation_link,
        "email_sent": email_sent,
    }


@router.get("/activate-password", response_class=HTMLResponse)
async def activate_password_form(token: str = ""):
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

