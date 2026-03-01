from fastapi import APIRouter

from . import auth, system

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(system.router, tags=["System"])

__all__ = ["router"]
