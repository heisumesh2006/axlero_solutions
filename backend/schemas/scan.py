from pydantic import BaseModel


class ScanCreate(BaseModel):
    target: str
    scan_type: str


class ScanResponse(BaseModel):
    id: int
    target: str
    scan_type: str
    status: str
    risk_score: int

    class Config:
        from_attributes = True