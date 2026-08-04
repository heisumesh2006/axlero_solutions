from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.database.session import SessionLocal
from backend.models.scan import Scan
from backend.schemas.scan import ScanCreate
from backend.schemas.scan import ScanResponse

from backend.models.finding import Finding
from backend.services.risk_engine import analyze_target



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

@router.post("/{scan_id}/analyze")
def analyze_scan(
    scan_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.user_id == int(current_user["sub"])
    ).first()

    if not scan:
        return {
            "error": "Scan not found"
        }

    result = analyze_target(scan.target)

    scan.status = "COMPLETED"
    scan.risk_score = result["risk_score"]

    for finding in result["findings"]:
        db.add(
            Finding(
                scan_id=scan.id,
                severity=result["threat_level"],
                description=finding
            )
        )

    db.commit()
    db.refresh(scan)

    return {
        "scan_id": scan.id,
        "status": scan.status,
        "risk_score": result["risk_score"],
        "threat_level": result["threat_level"],
        "findings": result["findings"]
    }