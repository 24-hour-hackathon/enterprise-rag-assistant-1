from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.services.ingestion import ingestion_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a new enterprise document"
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, DOCX, TXT), parse text, chunk, embed, and store in vector database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Validate file format and size
    try:
        file_ext = ingestion_service.validate_file(file.filename, file_size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save to disk
    file_path, stored_filename = ingestion_service.save_uploaded_file(file_bytes, file.filename)

    # Create initial DB record in PENDING status
    doc_record = Document(
        filename=file.filename,
        file_type=file_ext.lstrip("."),
        file_path=file_path,
        status="PENDING",
        version=1,
        chunk_count=0
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # Process and index
    try:
        doc_record = ingestion_service.process_and_index_document(db, doc_record)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}"
        )

    return DocumentUploadResponse(
        id=doc_record.id,
        filename=doc_record.filename,
        status=doc_record.status,
        version=doc_record.version,
        chunk_count=doc_record.chunk_count,
        message="Document successfully uploaded and indexed."
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all indexed enterprise documents"
)
def list_documents(db: Session = Depends(get_db)):
    """Retrieve all documents in the knowledge base."""
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return DocumentListResponse(
        total=len(documents),
        documents=[DocumentResponse.model_validate(d) for d in documents]
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details by ID"
)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific document by its UUID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return DocumentResponse.model_validate(doc)


@router.post(
    "/{document_id}/reindex",
    response_model=DocumentUploadResponse,
    summary="Re-index an existing document"
)
def reindex_document(document_id: str, db: Session = Depends(get_db)):
    """
    Purge old vectors from vector database, re-parse and re-chunk the document,
    generate fresh embeddings, and increment the document version.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    try:
        updated_doc = ingestion_service.reindex_document(db, doc)
        return DocumentUploadResponse(
            id=updated_doc.id,
            filename=updated_doc.filename,
            status=updated_doc.status,
            version=updated_doc.version,
            chunk_count=updated_doc.chunk_count,
            message=f"Document re-indexed successfully (Version {updated_doc.version})."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-indexing failed: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete document from knowledge base"
)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete document, its associated vector embeddings from ChromaDB,
    and remove the stored file from disk.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    ingestion_service.delete_document(db, doc)
    return {"message": f"Document '{document_id}' and all associated vector embeddings deleted successfully."}
