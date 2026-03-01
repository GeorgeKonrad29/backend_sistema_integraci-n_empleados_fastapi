# Estructura del Backend API

Estructura profesional de FastAPI organizida según convenciones modernas de Python:

```
src/
├── worker.py              # Punto de entrada principal, ensamble de FastAPI
├── __init__.py           # Inicializador del módulo
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
│
└── routes/               # Endpoints y routers de FastAPI
    ├── __init__.py      # Agrupa todos los routers
    ├── auth.py          # Endpoints de autenticación (/auth/login)
    └── system.py        # Endpoints de sistema (/, /hi, /env, /database/tables)
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

1. **Crear archivo en `routes/`** (ej: `routes/empleados.py`)
2. **Definir router y endpoints**
3. **Importar en `routes/__init__.py`** e incluirlo en el main router
4. **Listo**, se auto-registran en FastAPI

Ejemplo:

```python
# routes/empleados.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/list")
async def list_empleados():
    return {"empleados": []}
```

```python
# routes/__init__.py - agregar
router.include_router(empleados.router, prefix="/empleados", tags=["Empleados"])
```

## Agregar nuevos modelos

1. Crear archivo en `models/` (similar a `auth.py`)
2. Exportar en `models/__init__.py`
3. Usar en rutas: `from ..models import TuModelo`
