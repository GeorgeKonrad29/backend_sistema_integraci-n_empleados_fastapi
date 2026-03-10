"""Utilidades compartidas para autenticación."""
import json
from fastapi import HTTPException, Request

try:
    from utils.resend import fetch as fetch_resend_api_key
except ImportError:
    from ....utils.resend import fetch as fetch_resend_api_key


ACTIVATION_TOKEN_TTL_SECONDS = 3600
ACCESS_TOKEN_TTL_SECONDS = 3600
RESEND_FROM_EMAIL = "onboarding@resend.dev"


async def get_jwt_secret(req: Request) -> str:
    """Obtiene el JWT secret del entorno."""
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


async def ensure_activation_table(db):
    """Crea la tabla de activación de usuarios si no existe."""
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
    """Envía email de activación de cuenta."""
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
