from pydantic import BaseModel


class FindingResponse(BaseModel):
    id: int
    scan_id: int
    severity: str
    description: str

    class Config:
        from_attributes = True