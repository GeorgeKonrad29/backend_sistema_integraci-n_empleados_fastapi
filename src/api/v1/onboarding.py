from typing import Annotated
from fastapi import APIRouter, HTTPException, Request, Header

try:
    from models.onboarding import OnboardingRequest, OnboardingResponse
    from utils import decode_access_token
except ImportError:
    from ...models.onboarding import OnboardingRequest, OnboardingResponse
    from ...utils import decode_access_token

ALLOWED_ROLES = [1, 7, 24]  # IDs de cargo permitidos

router = APIRouter(tags=["onboarding"])


async def get_jwt_secret(req: Request) -> str:
    env = req.scope["env"]

    jwt_secret = getattr(env, "JWT_SECRET", None)
    if isinstance(jwt_secret, str) and jwt_secret.strip():
        return jwt_secret

    secret_binding = getattr(env, "jwt_secret", None)
    if secret_binding and hasattr(secret_binding, "get"):
        fetched_secret = await secret_binding.get()
        if fetched_secret and str(fetched_secret).strip():
            return str(fetched_secret)

    raise HTTPException(
        status_code=500,
        detail="JWT secret no configurado en el entorno.",
    )


async def validate_jwt_and_cargo(authorization: str | None, req: Request) -> dict:
    """
    Valida JWT y verifica que el usuario tenga uno de los cargos permitidos.
    Retorna el payload decodificado.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta header Authorization")

    auth_parts = authorization.split(" ", 1)
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato de Authorization inválido")

    token = auth_parts[1]
    jwt_secret = await get_jwt_secret(req)

    try:
        payload = decode_access_token(token, jwt_secret)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user_cargo = payload.get("cargo")
    if user_cargo not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"No tiene permisos. Solo usuarios con cargo {ALLOWED_ROLES} pueden acceder."
        )

    return payload


@router.post("/", response_model=OnboardingResponse)
async def create_onboarding_request(payload: OnboardingRequest, req: Request, authorization: str | None = Header(default=None)):
    """
    Crea una nueva solicitud de onboarding. Protegido. Solo usuarios con cargo 1, 7 o 24.
    """
    jwt_payload = await validate_jwt_and_cargo(authorization, req)
    env = req.scope["env"]
    db = env.dataBase

    try:
        # Verificar si el empleado existe
        user_check = await db.prepare("SELECT id FROM USUARIO WHERE id = ?").bind(payload.id_empleado).first()
        
        if not user_check:
            raise HTTPException(
                status_code=404, 
                detail=f"Error: El empleado con ID {payload.id_empleado} no existe."
            )

        query = """
            INSERT INTO SOLICITUDES (
                id_empleado, 
                fecha_creacion,
                fecha_fin,
                estado,
                especificaciones,
                destinatario
            ) VALUES (?, datetime('now'), ?, ?, ?, ?)
            RETURNING *
        """
        
        result = await db.prepare(query).bind(
            payload.id_empleado,
            payload.fecha_fin.isoformat(),
            payload.estado.value,
            payload.especificaciones,
            payload.destinatario
        ).first()

        if not result:
            raise HTTPException(status_code=500, detail="Error al crear la solicitud")

        # Convertir a dict para manejar JsNull de Cloudflare D1 adecuadamente en entorno Pyodide
        try:
            # En pyodide, JsProxy no suele ser iterable directamente por dict()
            # Intentamos usar to_py() si está disponible (común en objetos JS proxy)
            if hasattr(result, "to_py"):
                result_dict = result.to_py()
            else:
                # Si no, usamos los atributos conocidos de la tabla
                result_dict = {
                    "id": result.id,
                    "id_empleado": result.id_empleado,
                    "fecha_creacion": result.fecha_creacion,
                    "fecha_fin": result.fecha_fin,
                    "estado": result.estado,
                    "especificaciones": result.especificaciones,
                    "destinatario": result.destinatario,
                }
        except Exception as conv_err:
            raise HTTPException(
                status_code=500, 
                detail=f"Error convirtiendo resultado de DB: {str(conv_err)}"
            )

        # Limpiar posibles JsNull que Pydantic no reconoce automáticamente en este entorno
        # El string "jsnull" es una representación común en este entorno
        clean_dict = {}
        for key, value in result_dict.items():
            if str(value) == "jsnull" or value is None:
                clean_dict[key] = None
            else:
                clean_dict[key] = value

        return OnboardingResponse.model_validate(clean_dict)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error en la base de datos: {str(e)}"
        )


@router.get("/", response_model=list[OnboardingResponse])
async def list_onboarding_requests(req: Request, authorization: str | None = Header(default=None)):
    """
    Lista todas las solicitudes de onboarding. Protegido. Solo usuarios con cargo 1, 7 o 24.
    """
    jwt_payload = await validate_jwt_and_cargo(authorization, req)
    env = req.scope["env"]
    db = env.dataBase

    try:
        query_result = await db.prepare("SELECT * FROM SOLICITUDES ORDER BY fecha_creacion DESC").all()
        
        # Procesamos cada fila para limpiar posibles JsNull y convertirlos a dict compatibles
        final_list = []
        for row in query_result.results:
            row_dict = {}
            # En pyodide, podemos convertir JsProxy a dict mediante to_py si está disponible
            if hasattr(row, "to_py"):
                row_dict = row.to_py()
            else:
                # O acceder manualmente (asumiendo que las columnas son conocidas)
                row_dict = {
                    "id": row.id,
                    "id_empleado": row.id_empleado,
                    "fecha_creacion": row.fecha_creacion,
                    "fecha_fin": row.fecha_fin,
                    "estado": row.estado,
                    "especificaciones": row.especificaciones,
                    "destinatario": row.destinatario,
                }
            
            # Limpiamos los JsNull (ej: "jsnull" o None real)
            row_clean = {}
            for key, val in row_dict.items():
                if str(val) == "jsnull" or val is None:
                    row_clean[key] = None
                else:
                    row_clean[key] = val
            
            final_list.append(row_clean)
            
        return final_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener solicitudes: {str(e)}"
        )