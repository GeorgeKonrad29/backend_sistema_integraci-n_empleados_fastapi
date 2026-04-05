from fastapi import APIRouter

from .create import create_onboarding_request, router as create_router
from .dotacion import create_dotacion_template, router as dotacion_router
from .history import get_onboarding_request_history, router as history_router
from .list import (
    list_assigned_onboarding_requests,
    list_onboarding_requests,
    list_team_onboarding_requests,
    router as list_router,
)
from .update import router as update_router, update_onboarding_request

router = APIRouter()
router.include_router(dotacion_router)
router.include_router(create_router)
router.include_router(list_router)
router.include_router(update_router)
router.include_router(history_router)

__all__ = [
    "router",
    "create_dotacion_template",
    "create_onboarding_request",
    "list_onboarding_requests",
    "list_team_onboarding_requests",
    "list_assigned_onboarding_requests",
    "update_onboarding_request",
    "get_onboarding_request_history",
]
