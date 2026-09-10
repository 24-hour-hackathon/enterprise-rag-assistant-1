from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question to ask the knowledge base")
    top_k: Optional[int] = Field(None, description="Optional override for top K retrieved chunks")


class SourceReference(BaseModel):
    document: str = Field(..., description="Document filename")
    document_id: Optional[str] = Field(None, description="Document UUID")
    page: Optional[int] = Field(None, description="Page number (1-indexed) if applicable")
    section: Optional[str] = Field(None, description="Section heading or title")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    supporting_text: str = Field(..., description="Extracted source passage")
    relevance_score: Optional[float] = Field(None, description="Similarity or relevance score")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Concise document-grounded answer or unsupported message")
    has_answer: bool = Field(..., description="True if answer is supported by the knowledge base")
    sources: List[SourceReference] = Field(default_factory=list, description="List of source citations")
    query_id: Optional[str] = Field(None, description="Logged query ID for auditing")
    provider: Optional[str] = Field(None, description="Active LLM provider or fallback indicator")
