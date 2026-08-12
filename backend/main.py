"""SupplyPrescript FastAPI application."""

from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from ml.predict import predict_delay_days, predict_delay_probability
from ml.retraining import get_retraining_status, retrain_models
from models import Decision, ModelFeedback, Outcome, Shipment
from optimization.optimizer import generate_prescriptions_from_shipment


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SupplyPrescript API",
    description="Closed-loop prescriptive analytics for supply-chain operations.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DbSession = Annotated[Session, Depends(get_db)]


class OrmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ShipmentCreate(BaseModel):
    shipment_id: str = Field(min_length=1, max_length=100)
    country: str
    vendor: str
    product_group: str
    shipment_mode: str
    line_item_quantity: float = Field(ge=0)
    line_item_value: float = Field(ge=0)
    weight: float | None = Field(default=None, ge=0)
    freight_cost: float | None = Field(default=None, ge=0)
    scheduled_delivery_date: date
    available_budget: float = Field(ge=0)


class ShipmentResponse(ShipmentCreate, OrmResponse):
    id: int
    created_at: datetime


class PrescriptionRequest(BaseModel):
    country: str
    managed_by: str
    fulfill_via: str
    vendor_inco_term: str
    shipment_mode: str
    product_group: str
    sub_classification: str
    vendor: str
    brand: str
    dosage_form: str
    manufacturing_site: str
    first_line_designation: str
    line_item_quantity: float = Field(ge=0)
    line_item_value: float = Field(ge=0)
    weight: float | None = Field(default=None, ge=0)
    freight_cost: float | None = Field(default=None, ge=0)
    scheduled_delivery_date: date
    available_budget: float = Field(ge=0)
    minimum_inventory: float = Field(default=0, ge=0)

    def to_ml_features(self) -> dict:
        return {
            "Country": self.country,
            "Managed By": self.managed_by,
            "Fulfill Via": self.fulfill_via,
            "Vendor INCO Term": self.vendor_inco_term,
            "Shipment Mode": self.shipment_mode,
            "Product Group": self.product_group,
            "Sub Classification": self.sub_classification,
            "Vendor": self.vendor,
            "Brand": self.brand,
            "Dosage Form": self.dosage_form,
            "Manufacturing Site": self.manufacturing_site,
            "First Line Designation": self.first_line_designation,
            "Line Item Quantity": self.line_item_quantity,
            "Line Item Value": self.line_item_value,
            "Weight (Kilograms)": self.weight,
            "Freight Cost (USD)": self.freight_cost,
            "Scheduled Delivery Date": self.scheduled_delivery_date.isoformat(),
        }


class DecisionCreate(BaseModel):
    shipment_id: str
    selected_option: str
    option_title: str
    predicted_delay_probability: float = Field(ge=0, le=1)
    predicted_delay_days: float
    predicted_cost: float = Field(ge=0)
    available_budget: float = Field(ge=0)


class DecisionResponse(DecisionCreate, OrmResponse):
    id: int
    decision_status: str
    executed_at: datetime


class OutcomeCreate(BaseModel):
    decision_id: int
    actual_cost: float = Field(ge=0)
    actual_delay_days: float


class OutcomeResponse(OutcomeCreate, OrmResponse):
    id: int
    success: bool
    evaluated_at: datetime


def _risk_level(probability: float) -> str:
    if probability >= 0.70:
        return "HIGH"
    if probability >= 0.40:
        return "MEDIUM"
    return "LOW"


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "SupplyPrescript API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/prescribe")
def prescribe(payload: PrescriptionRequest) -> dict:
    features = payload.to_ml_features()
    probability = float(predict_delay_probability(features))
    delay_days = float(predict_delay_days(features))
    shipment_cost = payload.line_item_value + max(payload.freight_cost or 0.0, 0.0)
    recommendations = generate_prescriptions_from_shipment(
        shipment=features,
        shipment_cost=shipment_cost,
        available_budget=payload.available_budget,
        minimum_inventory=payload.minimum_inventory,
    )
    return {
        "prediction": {
            "delay_probability": probability,
            "predicted_delay_days": delay_days,
            "risk_level": _risk_level(probability),
        },
        "recommendations": recommendations,
    }


@app.post("/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(payload: ShipmentCreate, db: DbSession) -> Shipment:
    shipment = Shipment(**payload.model_dump())
    db.add(shipment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="shipment_id already exists")
    db.refresh(shipment)
    return shipment


@app.post("/decisions", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(payload: DecisionCreate, db: DbSession) -> Decision:
    option = payload.selected_option.upper()
    if option not in {"A", "B", "C"}:
        raise HTTPException(status_code=400, detail="selected_option must be A, B, or C")
    if payload.predicted_cost > payload.available_budget:
        raise HTTPException(status_code=400, detail="predicted_cost exceeds available_budget")
    shipment = db.scalar(select(Shipment).where(Shipment.shipment_id == payload.shipment_id))
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    decision = Decision(
        **payload.model_dump(exclude={"selected_option"}),
        selected_option=option,
        decision_status="EXECUTED",
        executed_at=datetime.utcnow(),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@app.get("/decisions", response_model=list[DecisionResponse])
def get_decisions(db: DbSession) -> list[Decision]:
    return list(
        db.scalars(
            select(Decision)
            .where(Decision.decision_status == "EXECUTED")
            .order_by(Decision.executed_at.desc())
        )
    )


@app.post("/outcomes", response_model=OutcomeResponse, status_code=status.HTTP_201_CREATED)
def create_outcome(payload: OutcomeCreate, db: DbSession) -> Outcome:
    decision = db.get(Decision, payload.decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    success = (
        payload.actual_delay_days <= decision.predicted_delay_days
        and payload.actual_cost <= decision.predicted_cost * 1.10
    )
    outcome = Outcome(**payload.model_dump(), success=success, evaluated_at=datetime.utcnow())
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


@app.post("/evaluate/{decision_id}")
def evaluate_decision(decision_id: int, db: DbSession) -> dict:
    decision = db.get(Decision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    outcome = db.scalar(
        select(Outcome)
        .where(Outcome.decision_id == decision_id)
        .order_by(Outcome.evaluated_at.desc())
    )
    if outcome is None:
        raise HTTPException(status_code=404, detail="Outcome not found for this decision")

    cost_error = outcome.actual_cost - decision.predicted_cost
    delay_error = outcome.actual_delay_days - decision.predicted_delay_days
    feedback = ModelFeedback(
        decision_id=decision.id,
        predicted_cost=decision.predicted_cost,
        actual_cost=outcome.actual_cost,
        cost_error=cost_error,
        predicted_delay_days=decision.predicted_delay_days,
        actual_delay_days=outcome.actual_delay_days,
        delay_error=delay_error,
    )
    db.add(feedback)
    db.commit()
    retraining_status = get_retraining_status(db.get_bind())
    return {
        "decision_id": decision.id,
        "predicted_cost": decision.predicted_cost,
        "actual_cost": outcome.actual_cost,
        "cost_error": cost_error,
        "predicted_delay_days": decision.predicted_delay_days,
        "actual_delay_days": outcome.actual_delay_days,
        "delay_error": delay_error,
        "success": outcome.success,
        "retraining_required": retraining_status["retraining_required"],
    }


@app.get("/retraining/status")
def retraining_status(db: DbSession) -> dict:
    return get_retraining_status(db.get_bind())


@app.post("/retraining/run")
def run_retraining(db: DbSession) -> dict:
    current_status = get_retraining_status(db.get_bind())
    if not current_status["retraining_required"]:
        return {"status": "not_required", "reason": current_status["reason"]}
    try:
        result = retrain_models(db.get_bind())
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Retraining failed safely: {error}")
    return {"status": "completed", **result}


@app.get("/analytics")
def analytics(db: DbSession) -> dict:
    total_decisions = db.scalar(select(func.count(Decision.id))) or 0
    successful_decisions = db.scalar(
        select(func.count(func.distinct(Outcome.decision_id))).where(Outcome.success.is_(True))
    ) or 0

    def average(model, column) -> float:
        return float(db.scalar(select(func.avg(column)).select_from(model)) or 0.0)

    learning = get_retraining_status(db.get_bind())
    return {
        "total_decisions": total_decisions,
        "successful_decisions": successful_decisions,
        "success_rate": successful_decisions / total_decisions if total_decisions else 0.0,
        "average_predicted_cost": average(Decision, Decision.predicted_cost),
        "average_actual_cost": average(Outcome, Outcome.actual_cost),
        "average_cost_error": average(ModelFeedback, ModelFeedback.cost_error),
        "average_predicted_delay": average(Decision, Decision.predicted_delay_days),
        "average_actual_delay": average(Outcome, Outcome.actual_delay_days),
        "average_delay_error": average(ModelFeedback, ModelFeedback.delay_error),
        "feedback_records": learning["feedback_records"],
        "mean_cost_error": learning["mean_cost_error"],
        "mean_delay_error": learning["mean_delay_error"],
        "retraining_required": learning["retraining_required"],
        "model_version": learning["model_version"],
    }
