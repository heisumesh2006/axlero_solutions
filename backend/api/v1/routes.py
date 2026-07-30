from fastapi import APIRouter

from backend.core.logger import logger
from fastapi import Depends

from backend.core.auth import get_current_user

router = APIRouter(
    prefix="/api/v1",
    tags=["Version 1"]
)


@router.get("/health")
def health():
    logger.info("Health endpoint accessed")

    return {
        "status": "healthy",
        "service": "Axlero API"
    }

@router.get("/protected")
def protected(current_user=Depends(get_current_user)):
    return {
        "message": "You have access to Axlero",
        "user": current_user
    }