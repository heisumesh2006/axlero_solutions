from fastapi import FastAPI

from backend.api.v1.routes import router
from backend.core.logger import logger
from backend.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

logger.info("Starting Axlero API")

app.include_router(router)


@app.get("/")
def home():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }