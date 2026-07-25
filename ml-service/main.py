from fastapi import FastAPI

from optimization.routes import router as optimization_router
from prediction.routes import prediction_service, router

app = FastAPI(title="SupplyPrescript ML Service")
app.include_router(router)
app.include_router(optimization_router)


@app.on_event("startup")
def load_prediction_artifacts() -> None:
    """Load prediction artifacts before the service accepts requests."""
    prediction_service.load_model()


@app.get("/")
def health_check() -> dict[str, str]:
    """Report that the ML service is running."""
    return {"status": "SupplyPrescript ML Service is running"}
