from fastapi import APIRouter

from . import auth, system, onboarding

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
router.include_router(system.router, tags=["System"])

__all__ = ["router"]
