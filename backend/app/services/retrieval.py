import logging
from typing import List, Optional
from dataclasses import dataclass
from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int]
    section: Optional[str]
    text: str
    distance: float
    similarity_score: float
    is_relevant: bool


class RetrievalService:
    def __init__(
        self,
        top_k: int = settings.TOP_K_RETRIEVAL,
        similarity_threshold: float = settings.SIMILARITY_THRESHOLD
    ):
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve_relevant_chunks(
        self,
        question: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[RetrievedChunk]:
        """
        Retrieve candidate chunks, compute relevance, and filter out low-relevance noise.
        """
        k = top_k if top_k is not None else self.top_k
        cutoff = threshold if threshold is not None else self.similarity_threshold

        if not question or not question.strip():
            return []

        # 1. Generate query embedding
        query_embedding = embedding_service.embed_query(question.strip())

        # 2. Query vector store
        query_res = vector_store_service.query_similarity(
            query_embedding=query_embedding,
            top_k=k
        )

        ids = query_res.get("ids", [[]])[0]
        docs = query_res.get("documents", [[]])[0]
        metadatas = query_res.get("metadatas", [[]])[0]
        distances = query_res.get("distances", [[]])[0]

        if not ids:
            logger.info(f"No chunks found in vector database for query: '{question}'")
            return []

        retrieved: List[RetrievedChunk] = []

        for i in range(len(ids)):
            chunk_id = ids[i]
            text = docs[i] if i < len(docs) else ""
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = float(distances[i]) if i < len(distances) else 1.0

            # In ChromaDB with cosine metric (HNWS cosine space):
            # vectors are normalized, cosine_distance = 1 - cosine_similarity
            # cosine_similarity = 1 - distance (clamped to [0.0, 1.0])
            sim_score = max(0.0, min(1.0, 1.0 - dist))

            # Relevance check: similarity score must meet or exceed threshold
            is_relevant = sim_score >= cutoff

            retrieved.append(RetrievedChunk(
                chunk_id=chunk_id,
                document_id=str(meta.get("document_id", "")),
                filename=str(meta.get("filename", "unknown")),
                page_number=meta.get("page_number", 1),
                section=meta.get("section", "General"),
                text=text,
                distance=dist,
                similarity_score=round(sim_score, 4),
                is_relevant=is_relevant
            ))

        # Filter strictly for relevant chunks so that irrelevant chunks are NOT sent to LLM
        relevant_chunks = [c for c in retrieved if c.is_relevant]

        logger.info(
            f"Retrieved {len(retrieved)} candidate chunks for question '{question}', "
            f"{len(relevant_chunks)} passed relevance threshold {cutoff}"
        )

        return relevant_chunks


retrieval_service = RetrievalService()
