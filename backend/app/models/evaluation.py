import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float
from app.core.database import Base


def utcnow_datetime():
    return datetime.now(timezone.utc)


class EvaluationMetric(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    generated_answer = Column(Text, nullable=False)
    is_grounded = Column(Boolean, nullable=False, default=True)
    precision_score = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow_datetime, nullable=False)

    def __repr__(self) -> str:
        return f"<EvaluationMetric id={self.id} is_grounded={self.is_grounded}>"
