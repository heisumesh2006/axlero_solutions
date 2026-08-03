from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.database.session import SessionLocal
from backend.models.scan import Scan
from backend.schemas.scan import ScanCreate
from backend.schemas.scan import ScanResponse


router = APIRouter(
    prefix="/scans",
    tags=["Security Scans"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=ScanResponse
)
def create_scan(
    data: ScanCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    scan = Scan(
        target=data.target,
        scan_type=data.scan_type,
        status="PENDING",
        user_id=int(current_user["sub"])
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    return scan