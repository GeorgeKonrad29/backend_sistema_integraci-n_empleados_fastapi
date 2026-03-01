from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Modelo para solicitud de login"""
    correo: str
    contrasena: str


class LoginUser(BaseModel):
    """Modelo de usuario retornado en respuesta"""
    id: int
    correo: str
    rol: int | None = None
    nombre: str


class LoginResponse(BaseModel):
    """Modelo de respuesta de login"""
    status: str
    message: str
    user: LoginUser
