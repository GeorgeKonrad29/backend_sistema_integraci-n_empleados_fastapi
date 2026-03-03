from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Modelo para solicitud de login"""
    correo: str
    contrasena: str


class LoginUser(BaseModel):
    """Modelo de usuario retornado en respuesta"""
    ID: int
    Correo: str
    rol_sistema: str | None = None
    nombre: str


class LoginResponse(BaseModel):
    """Modelo de respuesta de login"""
    status: str
    message: str
    user: LoginUser


class SignupRequest(BaseModel):
    """Modelo para solicitud de registro"""
    correo: str
    nombre: str
    rol_sistema: str | None = 'Operador'


class SignupResponse(BaseModel):
    """Modelo de respuesta de registro"""
    status: str
    message: str
    user: LoginUser
    activation_link: str
    email_sent: bool = False


class ActivatePasswordRequest(BaseModel):
    """Modelo para activar cuenta definiendo contraseña"""
    token: str
    contrasena: str


class ActivatePasswordResponse(BaseModel):
    """Modelo de respuesta de activación"""
    status: str
    message: str
