from fastapi import FastAPI

from backend.api.v1.routes import router
from backend.core.logger import logger
from backend.core.config import settings
from backend.api.v1.auth import router as auth_router
import backend.models.user

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

logger.info("Starting Axlero API")

app.include_router(router)
app.include_router(auth_router)

@app.get("/")
def home():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }