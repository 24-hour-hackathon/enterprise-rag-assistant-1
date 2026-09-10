import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow_datetime():
    return datetime.now(timezone.utc)


class Query(Base):
    __tablename__ = "queries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    answered = Column(Boolean, nullable=False, default=False)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow_datetime, nullable=False)

    # Relationships
    sources = relationship("Source", back_populates="query", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Query id={self.id} answered={self.answered}>"


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    chunk_id = Column(String(100), nullable=False)
    source_text = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True)

    # Relationships
    query = relationship("Query", back_populates="sources")
    document = relationship("Document", back_populates="sources")

    def __repr__(self) -> str:
        return f"<Source chunk_id={self.chunk_id} doc_id={self.document_id} page={self.page_number}>"
