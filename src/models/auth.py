from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Modelo para solicitud de login"""
    correo: str
    contrasena: str


class LoginUser(BaseModel):
    """Modelo de usuario retornado en respuesta"""
    id: int
    correo: str
    rol: str | None = None
    nombre: str
    cargo: int | None = None


class LoginResponse(BaseModel):
    """Modelo de respuesta de login"""
    status: str
    message: str
    user: LoginUser
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SignupRequest(BaseModel):
    """Modelo para solicitud de registro"""
    correo: str
    nombre: str
    rol: str | None = "Operador"
    cargo: int | None = None


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
