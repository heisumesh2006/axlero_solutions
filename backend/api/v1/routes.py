from fastapi import APIRouter
from fastapi import Depends

from backend.core.auth import get_current_user
from backend.core.auth import require_role

router = APIRouter(
    prefix="/api/v1",
    tags=["Version 1"]
)


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Axlero API"
    }


@router.get("/protected")
def protected(
    current_user=Depends(get_current_user)
):
    return {
        "message": "You have access to Axlero",
        "user": current_user
    }


@router.get("/admin")
def admin(
    current_user=Depends(require_role("ADMIN"))
):
    return {
        "message": "Admin access granted",
        "user": current_user
    }


@router.get("/analyst")
def analyst(
    current_user=Depends(require_role("ANALYST"))
):
    return {
        "message": "Analyst access granted",
        "user": current_user
    }