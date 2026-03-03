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
            payload.fecha_maxima_cumplimiento.isoformat() if payload.fecha_maxima_cumplimiento else None,
            payload.especificaciones
        ).first()

        if not result:
            raise HTTPException(status_code=500, detail="Error al crear la solicitud")

        return result
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
        result = await db.prepare("SELECT * FROM SOLICITUDES ORDER BY fecha_creacion DESC").all()
        return result.results
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener solicitudes: {str(e)}"
        )