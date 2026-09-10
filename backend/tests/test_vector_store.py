from app.services.chunking import DocumentChunk
from app.services.vector_store import vector_store_service
from app.services.embeddings import embedding_service


def test_vector_store_crud():
    # 1. Reset collection
    vector_store_service.reset_collection()
    assert vector_store_service.get_total_chunks() == 0

    # 2. Add test chunks
    chunk1 = DocumentChunk(
        chunk_id="test_chunk_001",
        document_id="doc_abc",
        filename="leave_policy.txt",
        text="All employees receive 25 annual leave days per fiscal year.",
        page_number=1,
        section="Annual Leave",
        word_count=10,
        metadata={"document_id": "doc_abc", "filename": "leave_policy.txt", "page_number": 1, "section": "Annual Leave", "chunk_id": "test_chunk_001", "word_count": 10}
    )
    chunk2 = DocumentChunk(
        chunk_id="test_chunk_002",
        document_id="doc_xyz",
        filename="security_guide.txt",
        text="Multi-factor authentication (MFA) is mandatory for all internal accounts.",
        page_number=3,
        section="Authentication",
        word_count=10,
        metadata={"document_id": "doc_xyz", "filename": "security_guide.txt", "page_number": 3, "section": "Authentication", "chunk_id": "test_chunk_002", "word_count": 10}
    )

    added = vector_store_service.add_chunks([chunk1, chunk2])
    assert added == 2
    assert vector_store_service.get_total_chunks() == 2

    # 3. Query similarity
    query_emb = embedding_service.embed_query("How many vacation days do employees get?")
    res = vector_store_service.query_similarity(query_emb, top_k=1)
    
    retrieved_ids = res["ids"][0]
    assert len(retrieved_ids) == 1
    assert retrieved_ids[0] == "test_chunk_001"

    # 4. Delete chunks by document_id
    deleted = vector_store_service.delete_document_chunks("doc_abc")
    assert deleted == 1
    assert vector_store_service.get_total_chunks() == 1

    # Clean up remaining
    vector_store_service.delete_document_chunks("doc_xyz")
    assert vector_store_service.get_total_chunks() == 0
