from fastapi import FastAPI

from .routes import router


app = FastAPI(
    title="Sistema de Integración de Empleados",
    description="API para gestión de empleados, solicitudes y jerarquía",
    version="1.0.0",
)

app.include_router(router, prefix="/v1")
