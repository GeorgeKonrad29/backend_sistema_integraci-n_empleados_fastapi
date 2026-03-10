"""Módulo de autenticación: login y signin."""
from fastapi import APIRouter

from .login import router as login_router
from .signin import router as signin_router

router = APIRouter()

# Incluir ambos routers
router.include_router(login_router)
router.include_router(signin_router)

__all__ = ["router"]
