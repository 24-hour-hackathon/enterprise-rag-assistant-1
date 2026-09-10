from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    failed_documents: int
    total_chunks: int
    total_questions: int
    total_answered_questions: int


class EvaluationItem(BaseModel):
    id: str
    question: str
    generated_answer: str
    is_grounded: bool
    precision_score: Optional[float] = None
    latency_ms: Optional[float] = None
    created_at: datetime


class AdminEvaluationResponse(BaseModel):
    total_evaluated: int
    grounded_rate_percentage: float
    average_latency_ms: float
    recent_evaluations: List[EvaluationItem]
