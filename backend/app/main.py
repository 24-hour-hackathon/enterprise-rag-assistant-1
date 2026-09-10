import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.services.llm import get_llm_provider
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.api.evaluation import router as evaluation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag_assistant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing database schema...")
    init_db()
    
    # Safe diagnostic logging (Never expose API keys)
    gemini_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    key_present = bool(gemini_key.strip())
    active_provider = get_llm_provider()
    
    logger.info(
        f"[DIAGNOSTIC] Selected LLM Provider setting: '{settings.LLM_PROVIDER}' | "
        f"Gemini Model: '{settings.GEMINI_MODEL}' | "
        f"GEMINI_API_KEY present: {key_present} | "
        f"Active Provider Instance: '{active_provider.__class__.__name__}'"
    )
    
    logger.info(f"RAG Assistant backend started in '{settings.ENVIRONMENT}' mode.")
    yield
    logger.info("Shutting down RAG Assistant backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Enterprise Document Question-Answering Assistant with RAG. "
        "Allows users to ask natural-language questions over verified enterprise documents "
        "and returns concise, document-grounded answers with source citations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS for local development & browser clients
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]
if isinstance(settings.CORS_ORIGINS, list):
    for o in settings.CORS_ORIGINS:
        if o != "*" and o not in allowed_origins:
            allowed_origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Endpoint
@app.get("/", tags=["General"], summary="Root endpoint")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": "/health"
    }


# Health Check Endpoint
@app.get("/health", tags=["General"], summary="Health check endpoint")
def health_check():
    gemini_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    key_present = bool(gemini_key.strip())
    active_provider = get_llm_provider()
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "active_provider_instance": active_provider.__class__.__name__,
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_key_present": key_present
    }


# Include API Routers
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(evaluation_router, prefix=settings.API_V1_STR)
