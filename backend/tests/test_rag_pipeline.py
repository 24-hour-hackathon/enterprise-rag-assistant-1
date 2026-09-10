import pytest
from app.services.chunking import DocumentChunk
from app.services.vector_store import vector_store_service
from app.services.rag import rag_service


@pytest.mark.asyncio
async def test_rag_pipeline_supported_question():
    vector_store_service.reset_collection()

    chunk = DocumentChunk(
        chunk_id="travel_001",
        document_id="doc_travel",
        filename="Travel_Policy.pdf",
        text="Economy class airfare is approved for domestic flights under 5 hours.",
        page_number=2,
        section="Flight Bookings",
        word_count=10,
        metadata={"document_id": "doc_travel", "filename": "Travel_Policy.pdf", "page_number": 2, "section": "Flight Bookings", "chunk_id": "travel_001", "word_count": 10}
    )
    vector_store_service.add_chunks([chunk])

    response, latency_ms = await rag_service.answer_question("What class of airfare is approved for domestic flights?")
    
    assert response.has_answer is True
    assert len(response.sources) >= 1
    assert response.sources[0].document == "Travel_Policy.pdf"
    assert response.sources[0].page == 2
    assert response.sources[0].section == "Flight Bookings"
    assert latency_ms > 0

    vector_store_service.delete_document_chunks("doc_travel")


@pytest.mark.asyncio
async def test_rag_pipeline_unsupported_question():
    vector_store_service.reset_collection()

    # Question with empty vector database
    response, latency_ms = await rag_service.answer_question("What is the quantum computing strategy for next year?")
    
    assert response.has_answer is False
    assert len(response.sources) == 0
    assert "couldn't find sufficient information in the approved knowledge base" in response.answer.lower()
