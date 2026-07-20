from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {
        "message": "Supply Prescript API v1"
    }

@router.get("/health")
def health():
    return {
        "status": "healthy"
    }