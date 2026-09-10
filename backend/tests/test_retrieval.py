from app.services.chunking import DocumentChunk
from app.services.vector_store import vector_store_service
from app.services.retrieval import retrieval_service


def test_retrieval_and_relevance_filter():
    vector_store_service.reset_collection()

    chunk = DocumentChunk(
        chunk_id="policy_001",
        document_id="doc_leave",
        filename="leave_policy.pdf",
        text="Parental leave is granted for up to 16 continuous weeks with full salary compensation.",
        page_number=4,
        section="Parental Leave",
        word_count=13,
        metadata={"document_id": "doc_leave", "filename": "leave_policy.pdf", "page_number": 4, "section": "Parental Leave", "chunk_id": "policy_001", "word_count": 13}
    )
    vector_store_service.add_chunks([chunk])

    # Relevant query
    relevant_chunks = retrieval_service.retrieve_relevant_chunks("How long is parental leave?")
    assert len(relevant_chunks) == 1
    assert relevant_chunks[0].chunk_id == "policy_001"
    assert relevant_chunks[0].is_relevant is True
    assert relevant_chunks[0].page_number == 4
    assert relevant_chunks[0].section == "Parental Leave"
    assert "Parental leave" in relevant_chunks[0].text

    # Semantic synonym query (e.g. "maternity/paternity time off" for "Parental leave")
    synonym_chunks = retrieval_service.retrieve_relevant_chunks("How many weeks off for new parents?")
    assert len(synonym_chunks) == 1
    assert synonym_chunks[0].chunk_id == "policy_001"

    # Completely irrelevant query to verify filtering
    irrelevant_chunks = retrieval_service.retrieve_relevant_chunks(
        question="What is the recipe for chocolate chip cookies?"
    )
    assert len(irrelevant_chunks) == 0

    vector_store_service.delete_document_chunks("doc_leave")
