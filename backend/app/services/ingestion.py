import os
import uuid
import logging
from pathlib import Path
from typing import Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import Document
from app.utils.file_parser import parse_file, ExtractedDocument
from app.services.chunking import chunking_service
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)


class IngestionService:
    @staticmethod
    def validate_file(filename: str, file_size: int) -> str:
        """Validate filename extension and file size limit."""
        extension = Path(filename).suffix.lower()
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file format '{extension}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(
                f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

        return extension

    @staticmethod
    def save_uploaded_file(file_bytes: bytes, original_filename: str) -> Tuple[str, str]:
        """Save file with a sanitized unique name to the upload directory."""
        # Sanitize filename: remove path traversal characters
        safe_name = os.path.basename(original_filename).replace(" ", "_")
        unique_prefix = uuid.uuid4().hex[:8]
        stored_filename = f"{unique_prefix}_{safe_name}"
        file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return file_path, stored_filename

    def process_and_index_document(self, db: Session, doc_record: Document) -> Document:
        """
        Extract text, chunk, embed, and index document chunks into ChromaDB.
        Updates document status in database.
        """
        try:
            logger.info(f"Beginning ingestion for Document ID: {doc_record.id}, file: {doc_record.filename}")

            # 1. Parse document text and pages
            extracted_doc: ExtractedDocument = parse_file(
                doc_record.file_path,
                original_filename=doc_record.filename
            )

            # 2. Split into chunks
            chunks = chunking_service.chunk_document(extracted_doc, document_id=doc_record.id)

            if not chunks:
                logger.warning(f"No textual content could be extracted from {doc_record.filename}")
                doc_record.status = "FAILED"
                doc_record.error_message = "No text could be extracted from document."
                doc_record.chunk_count = 0
                db.commit()
                db.refresh(doc_record)
                return doc_record

            # 3. Add chunks to ChromaDB (handles embedding internally)
            indexed_count = vector_store_service.add_chunks(chunks)

            # 4. Update Document Record
            doc_record.status = "INDEXED"
            doc_record.chunk_count = indexed_count
            doc_record.error_message = None
            db.commit()
            db.refresh(doc_record)

            logger.info(f"Successfully indexed document {doc_record.id} with {indexed_count} chunks")
            return doc_record

        except Exception as e:
            logger.error(f"Failed to ingest document {doc_record.id}: {e}", exc_info=True)
            doc_record.status = "FAILED"
            doc_record.error_message = str(e)
            db.commit()
            db.refresh(doc_record)
            raise e

    def reindex_document(self, db: Session, doc_record: Document) -> Document:
        """
        Re-index an existing document:
        1. Remove old vectors from ChromaDB.
        2. Re-read and re-chunk.
        3. Re-insert vectors into ChromaDB.
        4. Increment version counter.
        """
        try:
            logger.info(f"Re-indexing Document ID: {doc_record.id} (Current version: {doc_record.version})")

            # 1. Purge old chunks from vector store
            vector_store_service.delete_document_chunks(doc_record.id)

            # 2. Re-parse and re-chunk
            extracted_doc = parse_file(
                doc_record.file_path,
                original_filename=doc_record.filename
            )
            chunks = chunking_service.chunk_document(extracted_doc, document_id=doc_record.id)

            # 3. Insert new vectors
            indexed_count = vector_store_service.add_chunks(chunks)

            # 4. Increment version and update status
            doc_record.version += 1
            doc_record.chunk_count = indexed_count
            doc_record.status = "INDEXED"
            doc_record.error_message = None
            db.commit()
            db.refresh(doc_record)

            logger.info(f"Document {doc_record.id} re-indexed successfully to version {doc_record.version}")
            return doc_record

        except Exception as e:
            logger.error(f"Failed to re-index document {doc_record.id}: {e}", exc_info=True)
            doc_record.status = "FAILED"
            doc_record.error_message = str(e)
            db.commit()
            db.refresh(doc_record)
            raise e

    def delete_document(self, db: Session, doc_record: Document) -> None:
        """Delete document from database, vector store, and filesystem."""
        logger.info(f"Deleting document ID: {doc_record.id}")

        # Delete chunks from ChromaDB
        vector_store_service.delete_document_chunks(doc_record.id)

        # Delete file from filesystem
        if os.path.exists(doc_record.file_path):
            try:
                os.remove(doc_record.file_path)
            except OSError as e:
                logger.warning(f"Could not remove file {doc_record.file_path}: {e}")

        # Delete from DB
        db.delete(doc_record)
        db.commit()


ingestion_service = IngestionService()
