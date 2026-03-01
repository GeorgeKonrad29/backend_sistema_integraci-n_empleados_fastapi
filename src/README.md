# Estructura del Backend API

Estructura profesional de FastAPI organizada con versionado explícito:

```
src/
├── worker.py             # Entry point de Cloudflare Worker
├── main.py               # App FastAPI y montaje de versiones
├── __init__.py           # Inicializador del módulo
│
├── api/                  # Versiones de API
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py   # Router agregado de v1
│       ├── auth.py       # Endpoints auth (/v1/auth/login)
│       └── system.py     # Endpoints sistema (/v1/...)
│
├── config/               # Configuración centralizada
│   └── __init__.py      # Constantes y settings de la aplicación
│
├── models/               # Esquemas Pydantic (validación de datos)
│   ├── __init__.py
│   └── auth.py          # Modelos de autenticación (LoginRequest, LoginResponse, etc)
│
├── utils/                # Funciones utilitarias y helpers
│   ├── __init__.py
│   └── password.py      # Funciones de hash y verificación de contraseñas
```

## Importaciones

Desde cualquier archivo dentro de `src/`:

```python
# Desde models
from ..models import LoginRequest, LoginResponse

# Desde utils
from ..utils import hash_password, verify_password

# Desde config
from ..config import PBKDF2_ITERATIONS
```

## Agregar nuevos endpoints

1. **Crear archivo en `api/v1/`** (ej: `api/v1/empleados.py`)
2. **Definir router y endpoints**
3. **Importar en `api/v1/__init__.py`** e incluirlo en el router v1
4. **Listo**, se auto-registran en FastAPI

Ejemplo:

```python
# api/v1/empleados.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/list")
async def list_empleados():
    return {"empleados": []}
```

```python
# api/v1/__init__.py - agregar
router.include_router(empleados.router, prefix="/empleados", tags=["Empleados"])
```

## Agregar nuevos modelos

1. Crear archivo en `models/` (similar a `auth.py`)
2. Exportar en `models/__init__.py`
3. Usar en rutas: `from ..models import TuModelo`
