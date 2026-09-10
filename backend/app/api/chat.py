import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.query import Query, Source
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import rag_service

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a document-grounded question to the knowledge base"
)
async def chat_with_documents(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process natural language question:
    1. Retrieve relevant grounded chunks.
    2. Enforce strict context boundaries.
    3. Generate concise answer via LLM.
    4. Compile source references.
    5. Log query and source citations to database.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        response, latency_ms = await rag_service.answer_question(
            question=request.question,
            top_k=request.top_k
        )

        # Log query to database
        query_record = Query(
            question=request.question.strip(),
            answer=response.answer,
            answered=response.has_answer,
            latency_ms=latency_ms
        )
        db.add(query_record)
        db.commit()
        db.refresh(query_record)

        # Log source citations if answer is supported
        if response.has_answer and response.sources:
            for src in response.sources:
                if src.document_id:
                    source_record = Source(
                        query_id=query_record.id,
                        document_id=src.document_id,
                        page_number=src.page,
                        section=src.section,
                        chunk_id=src.chunk_id,
                        source_text=src.supporting_text,
                        relevance_score=src.relevance_score
                    )
                    db.add(source_record)
            db.commit()

        # Attach logged query ID to response
        response.query_id = query_record.id

        return response

    except Exception as e:
        logger.error(f"Error processing chat question '{request.question}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )
