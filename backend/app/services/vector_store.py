import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.chunking import DocumentChunk
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)


class VectorStoreService:
    _instance = None
    _client = None
    _collection = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        persist_dir: str = settings.CHROMA_PERSIST_DIR,
        collection_name: str = settings.CHROMA_COLLECTION_NAME
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._init_client()

    def _init_client(self):
        os.makedirs(self.persist_dir, exist_ok=True)
        if self._client is None:
            logger.info(f"Initializing ChromaDB PersistentClient at {self.persist_dir}")
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            # cosine similarity space: metadata distance is 1 - cosine_similarity
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    @property
    def collection(self):
        if self._collection is None:
            self._init_client()
        return self._collection

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Add document chunks to ChromaDB vector collection."""
        if not chunks:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.text)
            # ChromaDB metadata values must be str, int, float, or bool
            clean_metadata = {
                "document_id": str(chunk.document_id),
                "filename": str(chunk.filename),
                "page_number": int(chunk.page_number) if chunk.page_number is not None else 1,
                "section": str(chunk.section) if chunk.section else "General",
                "chunk_id": str(chunk.chunk_id),
                "word_count": int(chunk.word_count)
            }
            metadatas.append(clean_metadata)

        # Generate embeddings
        embeddings = embedding_service.embed_documents(documents)

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"Successfully indexed {len(chunks)} chunks in collection '{self.collection_name}'")
        return len(chunks)

    def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks belonging to a document from ChromaDB."""
        try:
            # Query existing chunks by document_id metadata
            results = self.collection.get(
                where={"document_id": str(document_id)}
            )
            chunk_ids = results.get("ids", [])
            if chunk_ids:
                self.collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document_id '{document_id}' from vector store")
                return len(chunk_ids)
            return 0
        except Exception as e:
            logger.error(f"Error deleting chunks for document_id '{document_id}': {e}", exc_info=True)
            return 0

    def query_similarity(
        self,
        query_embedding: List[float],
        top_k: int = settings.TOP_K_RETRIEVAL,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search vector database by query embedding vector."""
        total_count = self.collection.count()
        if total_count == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        actual_k = min(top_k, total_count)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        return results

    def get_total_chunks(self) -> int:
        """Return total number of vector chunks indexed."""
        return self.collection.count()

    def reset_collection(self) -> None:
        """Reset the vector store collection (used for testing/cleanup)."""
        if self._client:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )


vector_store_service = VectorStoreService()
