"""Configuración de la aplicación"""

# Configuración de seguridad para password hashing
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 390000

__all__ = ["PBKDF2_ALGORITHM", "PBKDF2_ITERATIONS"]
