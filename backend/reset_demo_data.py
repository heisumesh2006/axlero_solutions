"""Clear operational demo records while preserving the database and schema.

This utility is intentionally not called by application startup. Run it
manually from the backend directory when a clean demonstration is needed:

    python reset_demo_data.py
"""

from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from database import engine
from models import Decision, ModelFeedback, Outcome, Shipment


TABLES_IN_DELETE_ORDER = (
    ("model_feedback", ModelFeedback),
    ("outcomes", Outcome),
    ("decisions", Decision),
    ("shipments", Shipment),
)


def _record_counts(session: Session) -> dict[str, int]:
    return {
        name: int(session.scalar(select(func.count()).select_from(model)) or 0)
        for name, model in TABLES_IN_DELETE_ORDER
    }


def reset_demo_data(database_engine: Engine = engine) -> tuple[dict[str, int], dict[str, int]]:
    """Delete demo rows transactionally and return counts before and after."""
    with Session(database_engine) as session:
        before = _record_counts(session)
        try:
            for _name, model in TABLES_IN_DELETE_ORDER:
                session.execute(delete(model))
            session.commit()
        except Exception:
            session.rollback()
            raise
        after = _record_counts(session)

    print("Record counts before deletion:")
    for name, count in before.items():
        print(f"  {name}: {count}")
    print("Record counts after deletion:")
    for name, count in after.items():
        print(f"  {name}: {count}")
    print("Demo database reset successfully.")
    return before, after


if __name__ == "__main__":
    reset_demo_data()
