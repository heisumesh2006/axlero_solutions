# backend/app.py

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "SupplyPrescript API"}