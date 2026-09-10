import logging
from typing import List, Union
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name

    def _get_model(self):
        if self._model is None:
            logger.info(f"Loading sentence-transformers embedding model: {self.model_name}")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer: {e}. Checking fallback.", exc_info=True)
                raise RuntimeError(
                    f"Could not load embedding model '{self.model_name}'. "
                    f"Ensure sentence-transformers is installed: {e}"
                )
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text string."""
        if not text.strip():
            # Return zero vector for empty text
            return [0.0] * settings.EMBEDDING_DIMENSION
        model = self._get_model()
        vector = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vector.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a list of text strings."""
        if not texts:
            return []
        
        # Filter out completely empty strings for encoding but preserve indices
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generate normalized embedding for a search query."""
        return self.embed_text(query)


embedding_service = EmbeddingService()
