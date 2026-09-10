from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    status: str
    version: int = 1
    chunk_count: int = 0


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    version: int
    chunk_count: int
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_path: str
    status: str
    version: int
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]
