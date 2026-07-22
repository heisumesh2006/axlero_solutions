from fastapi import APIRouter

from backend.core.logger import logger

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