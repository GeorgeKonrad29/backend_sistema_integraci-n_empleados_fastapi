import json
import time

from fastapi import HTTPException, Request

try:
    from utils import hash_password
    from utils.resend import fetch as fetch_resend_api_key
except ImportError:
    from ...utils import hash_password
    from ...utils.resend import fetch as fetch_resend_api_key


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


async def send_activation_email(
    to_email: str, user_name: str, activation_link: str, req: Request
) -> bool:
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


async def activate_password_with_token(token: str, contrasena: str, req: Request) -> dict:
    env = req.scope["env"]
    db = env.dataBase

    await ensure_activation_table(db)

    now_ts = int(time.time())

    try:
        activation = (
            await db.prepare(
                "SELECT user_id, expires_at, used FROM ACTIVACION_USUARIO WHERE token = ? LIMIT 1"
            )
            .bind(token)
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

    password_hash = hash_password(contrasena)

    try:
        await db.prepare("UPDATE USUARIO SET contrasena = ? WHERE id = ?").bind(
            password_hash, activation.user_id
        ).run()
        await db.prepare("UPDATE ACTIVACION_USUARIO SET used = 1 WHERE token = ?").bind(
            token
        ).run()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activando usuario: {e}")

    return {"status": "ok", "message": "Contraseña activada correctamente"}