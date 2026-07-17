from fastapi import FastAPI

app = FastAPI(
    title="Supply Prescript API",
    version="1.0.0",
    description="Closed Loop Prescriptive Analytics"
)

@app.get("/")
def home():
    return {
        "message": "Supply Prescript API is Running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }