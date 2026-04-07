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
TEST_RECIPIENT_EMAIL = "jorgeluis57134@gmail.com"


def _resolve_resend_from_email(req: Request) -> str:
    env = req.scope["env"]
    configured = getattr(env, "RESEND_FROM_EMAIL", None)
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return RESEND_FROM_EMAIL


async def get_jwt_secret(req: Request) -> str:
    """Obtiene el JWT secret del entorno."""
    env = req.scope["env"]

    # Intentar con JWTSecret binding
    secret_binding = getattr(env, "JWTSecret", None)
    if secret_binding and hasattr(secret_binding, "get"):
        fetched_secret = await secret_binding.get()
        if fetched_secret and str(fetched_secret).strip():
            return str(fetched_secret)

    # Intentar con JWT_SECRET variable
    jwt_secret = getattr(env, "JWT_SECRET", None)
    if isinstance(jwt_secret, str) and jwt_secret.strip():
        return jwt_secret

    # Intentar con jwt_secret binding
    secret_binding = getattr(env, "jwt_secret", None)
    if secret_binding and hasattr(secret_binding, "get"):
        fetched_secret = await secret_binding.get()
        if fetched_secret and str(fetched_secret).strip():
            return str(fetched_secret)

    raise HTTPException(
        status_code=500,
        detail="JWT secret no configurado (buscó: JWTSecret, JWT_SECRET, jwt_secret).",
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


async def send_new_user_notification_email(
    req: Request,
    new_user_id: int,
    new_user_email: str,
    new_user_role: str,
    immediate_boss: str,
) -> bool:
    """Envía notificación de nuevo ingreso al correo de pruebas."""
    try:
        env = req.scope["env"]
        resend_api_key = await fetch_resend_api_key(req, env)
    except Exception:
        return False

    from_email = _resolve_resend_from_email(req)
    to_email = TEST_RECIPIENT_EMAIL
    if not resend_api_key or not from_email or not to_email:
        return False

    try:
        from pyodide.http import pyfetch
    except Exception:
        return False

    email_payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Nuevo ingreso de usuario",
        "html": (
            "<p>Se registró un nuevo usuario en el sistema.</p>"
            f"<p><strong>Jefe inmediato:</strong> {immediate_boss}</p>"
            f"<p><strong>ID:</strong> {new_user_id}<br>"
            f"<strong>Correo:</strong> {new_user_email}<br>"
            f"<strong>Rol:</strong> {new_user_role}</p>"
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

        if response.status in [200, 201, 202]:
            return True

        try:
            body_text = await response.text()
        except Exception:
            body_text = "<sin cuerpo>"

        print(
            f"[auth/signup] New-user notification rejected. status={response.status} "
            f"from={from_email} to={to_email} body={body_text}"
        )
        return False
    except Exception:
        return False

    from_email = _resolve_resend_from_email(req)
    if not resend_api_key or not from_email:
        return False

    try:
        from pyodide.http import pyfetch
    except Exception:
        return False

    original_to_email = to_email
    to_email = TEST_RECIPIENT_EMAIL

    email_payload = {
        "from": from_email,
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
        if original_to_email != to_email:
            print(
                f"[auth/signup] Redirecting activation email for testing. "
                f"requested_to={original_to_email} forced_to={to_email}"
            )

        response = await pyfetch(
            "https://api.resend.com/emails",
            method="POST",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            body=json.dumps(email_payload),
        )
        if response.status in [200, 201, 202]:
            return True

        try:
            body_text = await response.text()
        except Exception:
            body_text = "<sin cuerpo>"

        print(
            f"[auth/signup] Resend rejected email. status={response.status} "
            f"from={from_email} to={to_email} body={body_text}"
        )
        return False
    except Exception:
        return False
