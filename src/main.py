from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from api.v1 import router as v1_router
except ImportError:
    from .api.v1 import router as v1_router


app = FastAPI(
    title="Sistema de Integración de Empleados",
    description="API para gestión de empleados, solicitudes y jerarquía",
    version="1.0.0",
)

# Configuración CORS para permitir acceso desde Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sistema-integracion-empleados-qshx.vercel.app",
        "http://localhost:3000",  # Para desarrollo local
        "http://localhost:5173",  # Para Vite en desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

app.include_router(v1_router, prefix="/v1")
