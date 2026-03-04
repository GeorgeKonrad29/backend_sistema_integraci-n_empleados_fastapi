from typing import Annotated
from fastapi import APIRouter, HTTPException, Request

try:
    from models.onboarding import OnboardingRequest, OnboardingResponse
except ImportError:
    from ...models.onboarding import OnboardingRequest, OnboardingResponse


router = APIRouter(tags=["onboarding"])


@router.post("/", response_model=OnboardingResponse)
async def create_onboarding_request(payload: OnboardingRequest, req: Request):
    """
    Crea una nueva solicitud de onboarding.
    """
    env = req.scope["env"]
    db = env.dataBase

    try:
        # Verificar si el empleado existe
        user_check = await db.prepare("SELECT ID FROM USUARIO WHERE ID = ?").bind(payload.id_empleado).first()
        
        if not user_check:
            raise HTTPException(
                status_code=404, 
                detail=f"Error: El empleado con ID {payload.id_empleado} no existe."
            )

        query = """
            INSERT INTO SOLICITUDES (
                id_empleado, 
                id_area_encargada, 
                fecha_maxima_cumplimiento, 
                especificaciones
            ) VALUES (?, ?, ?, ?)
            RETURNING *
        """
        
        result = await db.prepare(query).bind(
            payload.id_empleado,
            payload.id_area_encargada,
            payload.fecha_maxima_cumplimiento.isoformat(),
            payload.especificaciones
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
                    "id_area_encargada": result.id_area_encargada,
                    "fecha_creacion": result.fecha_creacion,
                    "fecha_maxima_cumplimiento": result.fecha_maxima_cumplimiento,
                    "fecha_fin": result.fecha_fin,
                    "estado": result.estado,
                    "especificaciones": result.especificaciones
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
async def list_onboarding_requests(req: Request):
    """
    Lista todas las solicitudes de onboarding.
    """
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
                    "id_area_encargada": row.id_area_encargada,
                    "fecha_creacion": row.fecha_creacion,
                    "fecha_maxima_cumplimiento": row.fecha_maxima_cumplimiento,
                    "fecha_fin": row.fecha_fin,
                    "estado": row.estado,
                    "especificaciones": row.especificaciones
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