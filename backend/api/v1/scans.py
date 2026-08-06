from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.database.session import SessionLocal

from backend.models.scan import Scan
from backend.models.finding import Finding

from backend.schemas.scan import ScanCreate
from backend.schemas.scan import ScanResponse

from backend.services.risk_engine import analyze_target
from backend.services.ml_engine import predict_risk
from backend.services.recommendation_engine import get_recommendation


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

    ml_score = predict_risk(
        scan.target,
        scan.scan_type
    )

    final_score = min(
        result["risk_score"] + ml_score,
        100
    )

    if final_score >= 70:
        threat_level = "HIGH"
    elif final_score >= 40:
        threat_level = "MEDIUM"
    else:
        threat_level = "LOW"

    scan.status = "COMPLETED"
    scan.risk_score = final_score

    for finding in result["findings"]:
        db.add(
            Finding(
                scan_id=scan.id,
                severity=threat_level,
                description=finding
            )
        )

    db.commit()
    db.refresh(scan)

    recommendations = [
    get_recommendation(finding)
    for finding in result["findings"]
]

    return {
        "scan_id": scan.id,
        "status": scan.status,
        "risk_score": final_score,
        "threat_level": threat_level,
        "findings": result["findings"],
        "recommendations": recommendations
    }