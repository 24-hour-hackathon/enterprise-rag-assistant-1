import io
from app.services.vector_store import vector_store_service


def test_document_lifecycle_api(client):
    vector_store_service.reset_collection()

    # 1. Upload a text document
    file_content = b"# Remote Work Guidelines\n\nEmployees may work remotely up to two days per week with manager approval."
    upload_file = io.BytesIO(file_content)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("remote_work.txt", upload_file, "text/plain")}
    )

    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]
    assert data["filename"] == "remote_work.txt"
    assert data["status"] == "INDEXED"
    assert data["version"] == 1
    assert data["chunk_count"] >= 1

    # 2. Get document details
    get_res = client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == 200
    doc_data = get_res.json()
    assert doc_data["id"] == doc_id
    assert doc_data["file_type"] == "txt"

    # 3. List all documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == doc_id for d in list_data["documents"])

    # 4. Re-index document
    reindex_res = client.post(f"/api/documents/{doc_id}/reindex")
    assert reindex_res.status_code == 200
    reindex_data = reindex_res.json()
    assert reindex_data["version"] == 2
    assert reindex_data["status"] == "INDEXED"

    # 5. Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200

    # 6. Verify deletion
    verify_res = client.get(f"/api/documents/{doc_id}")
    assert verify_res.status_code == 404


def test_upload_invalid_file_extension(client):
    invalid_file = io.BytesIO(b"malicious executable content")
    response = client.post(
        "/api/documents/upload",
        files={"file": ("script.exe", invalid_file, "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]
