import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "Enterprise Document QA Assistant"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    # Storage Paths (resolved relative to backend directory if relative)
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'data' / 'app.db'}"
    CHROMA_PERSIST_DIR: str = str(BACKEND_DIR / "data" / "chroma")
    CHROMA_COLLECTION_NAME: str = "enterprise_documents"
    UPLOAD_DIR: str = str(BACKEND_DIR / "data" / "uploads")

    # Allowed File Extensions
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    MAX_UPLOAD_SIZE_MB: int = 25

    # Embedding Model Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Chunking Configuration
    CHUNK_TARGET_WORDS: int = 600
    CHUNK_OVERLAP_WORDS: int = 100

    # Retrieval Configuration
    TOP_K_RETRIEVAL: int = 4
    SIMILARITY_THRESHOLD: float = 0.35  # Minimum cosine similarity threshold (0.0 to 1.0)

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai", "anthropic"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0

    # Gemini Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=[str(BACKEND_DIR / ".env"), str(BACKEND_DIR.parent / ".env")],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent, exist_ok=True)
