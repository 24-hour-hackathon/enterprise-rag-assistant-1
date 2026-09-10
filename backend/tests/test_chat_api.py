import io
from app.services.vector_store import vector_store_service


def test_chat_api_grounded_answer(client):
    vector_store_service.reset_collection()

    # Upload knowledge document
    content = (
        "# Enterprise Expense Policy\n\n"
        "Daily meal allowance is capped at 75 USD per day during business travel."
    )
    upload_file = io.BytesIO(content.encode("utf-8"))
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("Expense_Policy.txt", upload_file, "text/plain")}
    )
    assert upload_res.status_code == 201

    # Ask question
    chat_res = client.post(
        "/api/chat",
        json={"question": "What is the daily meal allowance for business travel?"}
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()

    assert chat_data["has_answer"] is True
    assert "75 USD" in chat_data["answer"] or "meal allowance" in chat_data["answer"].lower() or "expense" in chat_data["answer"].lower()
    assert len(chat_data["sources"]) >= 1
    source = chat_data["sources"][0]
    assert source["document"] == "Expense_Policy.txt"
    assert source["page"] == 1
    assert "chunk_id" in source
    assert "supporting_text" in source


def test_chat_api_unsupported_question(client):
    vector_store_service.reset_collection()

    chat_res = client.post(
        "/api/chat",
        json={"question": "What is the secret recipe for the cafeteria soup?"}
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()

    assert chat_data["has_answer"] is False
    assert len(chat_data["sources"]) == 0
    assert "couldn't find sufficient information" in chat_data["answer"].lower()


def test_chat_api_semantic_synonym_retrieval(client):
    """
    Regression test:
    Verify that asking 'vacation days' correctly matches 'annual leave' (semantic equivalent),
    identifies 18 days, and returns supporting source citation.
    """
    vector_store_service.reset_collection()

    content = (
        "# Subramanya Employee Profile\n\n"
        "Employee ID: EMP1024\n"
        "Role: Senior Systems Engineer\n"
        "Department: Platform Infrastructure\n"
        "Employees are entitled to 18 days of annual leave per calendar year."
    )
    upload_file = io.BytesIO(content.encode("utf-8"))
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("Subramanya_Profile.txt", upload_file, "text/plain")}
    )
    assert upload_res.status_code == 201

    # Direct query test: verify concise answer (never full chunk dump)
    direct_res = client.post(
        "/api/chat",
        json={"question": "What is Subramanya's employee ID?"}
    )
    assert direct_res.status_code == 200
    direct_data = direct_res.json()
    assert direct_data["has_answer"] is True
    assert "EMP1024" in direct_data["answer"]
    assert len(direct_data["answer"].split("\n")) <= 2  # Concise answer
    # Ensure answer does not dump the entire chunk with role/department/leave
    assert "Platform Infrastructure" not in direct_data["answer"]
    assert len(direct_data["sources"]) >= 1
    # Full source text remains separately in sources array
    assert "EMP1024" in direct_data["sources"][0]["supporting_text"]

    # Semantic synonym query test: "vacation days" -> "annual leave"
    semantic_res = client.post(
        "/api/chat",
        json={"question": "How many vacation days does Subramanya get every year?"}
    )
    assert semantic_res.status_code == 200
    semantic_data = semantic_res.json()
    assert semantic_data["has_answer"] is True
    assert "18 days" in semantic_data["answer"] or "18" in semantic_data["answer"]
    assert "Senior Systems Engineer" not in semantic_data["answer"]  # Concise focused answer
    assert len(semantic_data["sources"]) >= 1
    assert semantic_data["sources"][0]["document"] == "Subramanya_Profile.txt"
    assert "annual leave" in semantic_data["sources"][0]["supporting_text"].lower()

    # Unsupported query test: "salary" is NOT in document -> must be rejected
    unsupported_res = client.post(
        "/api/chat",
        json={"question": "What is Subramanya's salary?"}
    )
    assert unsupported_res.status_code == 200
    unsupported_data = unsupported_res.json()
    assert unsupported_data["has_answer"] is False
    assert len(unsupported_data["sources"]) == 0
    assert "couldn't find sufficient information" in unsupported_data["answer"].lower()


def test_chat_api_concise_generic_qa(client):
    """Verify concise answers across generic non-Subramanya document queries."""
    vector_store_service.reset_collection()

    content = (
        "# Corporate Security Policy\n\n"
        "All employee passwords must be changed every 90 days without exception.\n"
        "Multi-factor authentication (MFA) is required on all workstations.\n"
        "Security badges must be visibly displayed at all times."
    )
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("Security_Policy.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    )
    assert upload_res.status_code == 201

    chat_res = client.post(
        "/api/chat",
        json={"question": "How often should passwords be changed?"}
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()

    assert chat_data["has_answer"] is True
    assert "90 days" in chat_data["answer"]
    # Ensure other unrelated sentences from the chunk are not dumped into the answer
    assert "Multi-factor authentication" not in chat_data["answer"]
    assert "Security badges" not in chat_data["answer"]
    # Sources contain the full chunk
    assert len(chat_data["sources"]) >= 1
    assert "Security_Policy.txt" == chat_data["sources"][0]["document"]


def test_chat_api_empty_question(client):
    chat_res = client.post(
        "/api/chat",
        json={"question": "   "}
    )
    assert chat_res.status_code == 422 or chat_res.status_code == 400

