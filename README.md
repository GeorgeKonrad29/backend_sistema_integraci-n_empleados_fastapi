# Sistema de Integración de Empleados

API construida con FastAPI y ejecutada en Cloudflare Workers (Python).

## Estado actual

- Autenticación JWT con Bearer token
- Control de acceso por cargo y permisos configurable
- Login, signup protegido, consulta de usuario actual y consulta de cargos
- Activación de contraseña por correo
- Integración con D1 para persistencia
- Integración con Secrets Store para credenciales sensibles

## Stack

- FastAPI
- Cloudflare Workers Python
- D1 Database
- Secrets Store
- Jinja2

## Estructura principal

- [src/main.py](src/main.py): instancia principal de FastAPI
- [src/worker.py](src/worker.py): entrada del Worker
- [src/api/v1](src/api/v1): routers de la API
- [src/utils/security.py](src/utils/security.py): JWT, Bearer y permisos
- [src/api/v1/auth](src/api/v1/auth): login, signup, cargos y activación

## Variables y secretos

El proyecto usa el binding de D1 `dataBase` y el Secrets Store `JWTSecret`.

Secretos/bindings esperados:

- `JWTSecret`: secreto JWT desde Cloudflare Secrets Store
- `resend`: API key de Resend desde Secrets Store

Si necesitas compatibilidad local, el código también intenta con:

- `JWT_SECRET`
- `jwt_secret`

## Base de datos

### Esquema

El esquema base está en [src/schema.sql](src/schema.sql).

Tablas principales:

- `JERARQUIA`
- `USUARIO`
- `PUESTO_DE_TRABAJO`
- `DOTACION`
- `SOLICITUDES`
- `HISTORIAL`

### Estructura organizacional

La estructura completa de cargos está en [estructura_organizacional.sql](estructura_organizacional.sql).

### Seed de dotación

La carga inicial de dotación está en [dotacion_seed.sql](dotacion_seed.sql).

## Autenticación

### Login

`POST /v1/auth/login`

Retorna:

- `access_token`
- `token_type`
- `expires_in`
- datos del usuario, incluido `cargo`

### Usuario actual

`GET /v1/auth/me`

Requiere `Authorization: Bearer <token>`.

### Signup

`POST /v1/auth/signup`

Protegido por permisos. Actualmente restringido a RRHH.

### Cargos

`GET /v1/auth/cargos`

Devuelve la jerarquía de cargos almacenada en la tabla `JERARQUIA`.

### Activación de contraseña

- `GET /v1/auth/activate-password`
- `POST /v1/auth/activate-password`

## Ejemplos de uso

### 1) Login

```bash
curl -X POST "https://TU-DOMINIO.workers.dev/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "rrhh@sinergia.com",
    "contrasena": "TU_PASSWORD"
  }'
```

Respuesta esperada:

```json
{
  "status": "ok",
  "message": "Login exitoso",
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2) Obtener usuario actual

```bash
curl -X GET "https://TU-DOMINIO.workers.dev/v1/auth/me" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

### 3) Crear usuario desde RRHH

```bash
curl -X POST "https://TU-DOMINIO.workers.dev/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN_DE_RRHH" \
  -d '{
    "nombre": "Juan Pérez",
    "correo": "juan.perez@empresa.com",
    "contrasena": "",
    "rol": "Operador",
    "cargo": 44
  }'
```

### 4) Consultar cargos

```bash
curl -X GET "https://TU-DOMINIO.workers.dev/v1/auth/cargos" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

### 5) Activar contraseña

```bash
curl -X POST "https://TU-DOMINIO.workers.dev/v1/auth/activate-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_DE_ACTIVACION",
    "contrasena": "NuevaClaveSegura123"
  }'
```

## Notas sobre permisos

Actualmente el acceso está controlado por cargo.

- `auth.signup` requiere RRHH
- `cargos.listar` permite RRHH e inventario
- `onboarding.crear` requiere RRHH
- `onboarding.listar` requiere RRHH

## Permisos configurables

Los permisos se administran en [src/utils/security.py](src/utils/security.py).

Mapas actuales:

- `ROLE_CARGO_ACCESS`
- `PERMISSION_ROLES`

Agregar un nuevo permiso consiste en:

1. Crear la llave en `PERMISSION_ROLES`
2. Asociarla a un rol funcional como `rrhh`
3. Definir los cargos permitidos en `ROLE_CARGO_ACCESS`

## Endpoints públicos

- `GET /v1/`
- `GET /v1/hi/{name}`
- `GET /v1/env`
- `GET /v1/database/tables`

## Desarrollo local

### Ejecutar pruebas

```bash
pytest
```

### Desplegar en Cloudflare

```bash
uv run pywrangler deploy
```

### Ejecutar localmente con Wrangler

```bash
uv run pywrangler dev
```

## Notas importantes

- El proyecto usa Cloudflare Workers Python, así que algunas dependencias y rutas de importación tienen manejo dual para entorno local y Cloudflare.
- Si el login o signup falla por secret, revisa que `JWTSecret` exista en el Secrets Store.
- Si cambias la estructura organizacional, sincroniza:
  - [estructura_organizacional.sql](estructura_organizacional.sql)
  - `ROLE_CARGO_ACCESS` en [src/utils/security.py](src/utils/security.py)
  - `dotacion_seed.sql` si aplica
