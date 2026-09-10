import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test configuration is set before importing app modules
os.environ["ENVIRONMENT"] = "testing"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app
from app.services.vector_store import vector_store_service
from app.services.llm import MockLLMProvider
from app.services.rag import rag_service

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Create temporary directories for test uploads and chroma DB."""
    temp_dir = tempfile.mkdtemp(prefix="rag_test_")
    test_upload_dir = os.path.join(temp_dir, "uploads")
    test_chroma_dir = os.path.join(temp_dir, "chroma")
    os.makedirs(test_upload_dir, exist_ok=True)
    os.makedirs(test_chroma_dir, exist_ok=True)

    settings.UPLOAD_DIR = test_upload_dir
    settings.CHROMA_PERSIST_DIR = test_chroma_dir
    settings.LLM_PROVIDER = "mock"

    # Reset vector store to test location
    vector_store_service.persist_dir = test_chroma_dir
    vector_store_service._client = None
    vector_store_service._collection = None
    vector_store_service._init_client()

    # Force mock LLM provider for tests
    rag_service._llm_provider = MockLLMProvider()

    yield

    # Teardown
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def db_session():
    """Provide a clean database session per test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
