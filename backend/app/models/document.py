import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow_datetime():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, INDEXED, FAILED
    version = Column(Integer, nullable=False, default=1)
    chunk_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow_datetime, nullable=False)
    updated_at = Column(DateTime, default=utcnow_datetime, onupdate=utcnow_datetime, nullable=False)

    # Relationships
    sources = relationship("Source", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status} version={self.version}>"
