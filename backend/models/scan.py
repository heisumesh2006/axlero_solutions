from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey

from datetime import datetime

from backend.database.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)

    target = Column(String(255), nullable=False)

    scan_type = Column(String(50), nullable=False)

    status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )

    risk_score = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )