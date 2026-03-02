import base64
import hashlib
import hmac
import secrets

try:
    from config import PBKDF2_ALGORITHM, PBKDF2_ITERATIONS
except ImportError:
    from ..config import PBKDF2_ALGORITHM, PBKDF2_ITERATIONS


def _pepper_password(password: str, pepper: str) -> bytes:
    return hmac.new(
        pepper.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).digest()


def hash_password(password: str, pepper: str) -> str:
    """
    Hashea una contraseña usando PBKDF2-SHA256 con salt aleatorio.
    
    Args:
        password: Contraseña en texto plano
        pepper: Secret de Cloudflare para endurecer el hash
    
    Returns:
        Contraseña hasheada en formato: pbkdf2_sha256$iteraciones$salt$hash
    """
    salt = secrets.token_hex(16)
    peppered_password = _pepper_password(password, pepper)
    derived_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        peppered_password,
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    encoded_key = base64.b64encode(derived_key).decode("utf-8")
    return f"pbkdf2_sha256_peppered${PBKDF2_ITERATIONS}${salt}${encoded_key}"


def verify_password(plain_password: str, stored_password: str, pepper: str) -> bool:
    """
    Verifica una contraseña en texto plano contra su hash almacenado.
    Soporta tanto contraseñas hasheadas como en texto plano (legado).
    
    Args:
        plain_password: Contraseña en texto plano a verificar
        stored_password: Contraseña almacenada (hash o texto plano)
        pepper: Secret de Cloudflare para validar hashes
    
    Returns:
        True si la contraseña es válida, False en caso contrario
    """
    if stored_password.startswith("pbkdf2_sha256_peppered$"):
        try:
            _, iterations, salt, stored_key = stored_password.split("$", 3)
            peppered_password = _pepper_password(plain_password, pepper)
            calculated_key = hashlib.pbkdf2_hmac(
                PBKDF2_ALGORITHM,
                peppered_password,
                salt.encode("utf-8"),
                int(iterations),
            )
            calculated_key_b64 = base64.b64encode(calculated_key).decode("utf-8")
            return hmac.compare_digest(calculated_key_b64, stored_key)
        except Exception:
            return False

    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, stored_key = stored_password.split("$", 3)
            calculated_key = hashlib.pbkdf2_hmac(
                PBKDF2_ALGORITHM,
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            calculated_key_b64 = base64.b64encode(calculated_key).decode("utf-8")
            return hmac.compare_digest(calculated_key_b64, stored_key)
        except Exception:
            return False

    return hmac.compare_digest(plain_password, stored_password)
