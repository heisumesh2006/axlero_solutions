from fastapi import FastAPI

from backend.api.v1.routes import router
from backend.core.logger import logger
from backend.core.config import settings
from backend.api.v1.auth import router as auth_router
import backend.models.user
from backend.api.v1.scans import router as scan_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("Starting Axlero API")

app.include_router(router)
app.include_router(auth_router)
app.include_router(scan_router)

@app.get("/")
def home():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }