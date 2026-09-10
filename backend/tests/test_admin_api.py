import io
from app.services.vector_store import vector_store_service


def test_admin_stats_and_evaluation(client):
    vector_store_service.reset_collection()

    # Get initial stats
    stats_res = client.get("/api/admin/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_documents" in stats
    assert "total_chunks" in stats
    assert "total_questions" in stats

    # Upload document
    doc_content = b"# Cybersecurity Policy\n\nPasswords must be changed every 90 days."
    client.post(
        "/api/documents/upload",
        files={"file": ("cybersecurity.txt", io.BytesIO(doc_content), "text/plain")}
    )

    # Ask chat question
    client.post(
        "/api/chat",
        json={"question": "How often should passwords be changed?"}
    )

    # Check updated stats
    updated_stats = client.get("/api/admin/stats").json()
    assert updated_stats["total_documents"] >= 1
    assert updated_stats["total_chunks"] >= 1
    assert updated_stats["total_questions"] >= 1

    # Check evaluation endpoint
    eval_res = client.get("/api/admin/evaluation")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "grounded_rate_percentage" in eval_data
    assert "average_latency_ms" in eval_data
