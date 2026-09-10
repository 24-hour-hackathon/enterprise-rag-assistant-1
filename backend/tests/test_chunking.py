from app.utils.file_parser import ExtractedDocument, ExtractedBlock
from app.services.chunking import ChunkingService


def test_chunking_small_document():
    service = ChunkingService(target_words=50, overlap_words=10)
    
    blocks = [
        ExtractedBlock(text="This is section one with some details about vacation policy.", page_number=1, section="Vacation"),
        ExtractedBlock(text="This is section two with details regarding reimbursement and expenses.", page_number=1, section="Expenses")
    ]
    doc = ExtractedDocument(filename="policy.txt", file_type="txt", blocks=blocks)

    chunks = service.chunk_document(doc, document_id="doc_123")
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.document_id == "doc_123"
    assert chunk.filename == "policy.txt"
    assert "vacation policy" in chunk.text
    assert chunk.metadata["page_number"] == 1


def test_chunking_large_document_with_overlap():
    service = ChunkingService(target_words=20, overlap_words=5)

    # 100 words text
    long_text = "word " * 100
    blocks = [
        ExtractedBlock(text=long_text, page_number=2, section="Deep Dive")
    ]
    doc = ExtractedDocument(filename="large.txt", file_type="txt", blocks=blocks)

    chunks = service.chunk_document(doc, document_id="doc_large")
    assert len(chunks) > 1
    
    for c in chunks:
        assert c.word_count <= 25
        assert c.document_id == "doc_large"
        assert c.page_number == 2
        assert c.section == "Deep Dive"
