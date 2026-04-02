from fastapi import APIRouter

from .onboarding import onboarding

from .auth import router as auth_router
from .puesto_trabajo import router as puesto_trabajo_router
from . import system

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(puesto_trabajo_router, prefix="/puesto-trabajo", tags=["PuestoTrabajo"])
router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
router.include_router(system.router, tags=["System"])

__all__ = ["router"]
