"""API routers package."""
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router

__all__ = ["documents_router", "chat_router", "admin_router"]
