from fastapi import FastAPI

from backend.api.v1.routes import router
from backend.core.logger import logger

app = FastAPI(
    title="Axlero API",
    version="1.0.0"
)

logger.info("Starting Axlero API")

app.include_router(router)


@app.get("/")
def home():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to Axlero"
    }