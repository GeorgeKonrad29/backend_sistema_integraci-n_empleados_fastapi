from fastapi import FastAPI

try:
    from api.v1 import router as v1_router
except ImportError:
    from .api.v1 import router as v1_router


app = FastAPI(
    title="Sistema de Integración de Empleados",
    description="API para gestión de empleados, solicitudes y jerarquía",
    version="1.0.0",
)

app.include_router(v1_router, prefix="/v1")
