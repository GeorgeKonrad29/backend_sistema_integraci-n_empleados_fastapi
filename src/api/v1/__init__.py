from fastapi import APIRouter

from .auth import router as auth_router
from . import system, onboarding

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
router.include_router(system.router, tags=["System"])

__all__ = ["router"]
