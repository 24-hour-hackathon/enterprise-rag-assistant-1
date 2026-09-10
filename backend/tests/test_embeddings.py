import numpy as np
from app.services.embeddings import embedding_service


def test_single_embedding_dimension():
    text = "Enterprise Document Question-Answering Assistant with RAG."
    vector = embedding_service.embed_text(text)
    assert isinstance(vector, list)
    assert len(vector) == 384
    # Check normalized vector (norm close to 1.0)
    norm = np.linalg.norm(vector)
    assert np.isclose(norm, 1.0, atol=1e-3)


def test_batch_embedding():
    texts = [
        "What is the company leave policy?",
        "How do I submit an expense report?"
    ]
    vectors = embedding_service.embed_documents(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


def test_empty_text_embedding():
    vector = embedding_service.embed_text("")
    assert len(vector) == 384
    assert all(v == 0.0 for v in vector)
