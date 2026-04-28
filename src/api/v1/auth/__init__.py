"""Módulo de autenticación: login y signin."""
from fastapi import APIRouter

from .login import router as login_router
from .signin import router as signin_router
from .cargos import router as cargos_router
from .delete import router as delete_router

router = APIRouter()

# Incluir todos los routers
router.include_router(login_router)
router.include_router(signin_router)
router.include_router(cargos_router)
router.include_router(delete_router)

__all__ = ["router"]
