from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.document import Document
from app.models.query import Query
from app.models.evaluation import EvaluationMetric
from app.schemas.admin import AdminStatsResponse, AdminEvaluationResponse, EvaluationItem
from app.services.vector_store import vector_store_service

router = APIRouter(prefix="/admin", tags=["Admin & Evaluation"])


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get system knowledge base statistics"
)
def get_system_stats(db: Session = Depends(get_db)):
    """Retrieve overall system statistics for documents, vectors, and query volume."""
    total_docs = db.query(Document).count()
    indexed_docs = db.query(Document).filter(Document.status == "INDEXED").count()
    failed_docs = db.query(Document).filter(Document.status == "FAILED").count()
    
    total_chunks = vector_store_service.get_total_chunks()
    total_queries = db.query(Query).count()
    answered_queries = db.query(Query).filter(Query.answered.is_(True)).count()

    return AdminStatsResponse(
        total_documents=total_docs,
        indexed_documents=indexed_docs,
        failed_documents=failed_docs,
        total_chunks=total_chunks,
        total_questions=total_queries,
        total_answered_questions=answered_queries
    )


@router.get(
    "/evaluation",
    response_model=AdminEvaluationResponse,
    summary="Get RAG grounding and latency evaluation metrics"
)
def get_evaluation_metrics(db: Session = Depends(get_db)):
    """Retrieve RAG pipeline evaluation metrics and grounding precision pass-rates."""
    evals = db.query(EvaluationMetric).order_by(EvaluationMetric.created_at.desc()).limit(50).all()
    total_evaluated = len(evals)

    if total_evaluated > 0:
        grounded_count = sum(1 for e in evals if e.is_grounded)
        grounded_rate = round((grounded_count / total_evaluated) * 100, 2)
        avg_latency = round(sum((e.latency_ms or 0) for e in evals) / total_evaluated, 2)
    else:
        # Fallback to query history if explicit evaluations haven't been logged yet
        queries = db.query(Query).all()
        total_q = len(queries)
        if total_q > 0:
            answered_q = sum(1 for q in queries if q.answered)
            grounded_rate = round((answered_q / total_q) * 100, 2)
            avg_latency = round(sum((q.latency_ms or 0) for q in queries) / total_q, 2)
        else:
            grounded_rate = 100.0
            avg_latency = 0.0

    eval_items = [
        EvaluationItem(
            id=e.id,
            question=e.question,
            generated_answer=e.generated_answer,
            is_grounded=e.is_grounded,
            precision_score=e.precision_score,
            latency_ms=e.latency_ms,
            created_at=e.created_at
        )
        for e in evals
    ]

    return AdminEvaluationResponse(
        total_evaluated=total_evaluated,
        grounded_rate_percentage=grounded_rate,
        average_latency_ms=avg_latency,
        recent_evaluations=eval_items
    )
