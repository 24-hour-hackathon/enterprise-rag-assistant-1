// Global Configuration for RAG Assistant Frontend
const CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8000",
  ENDPOINTS: {
    HEALTH: "/health",
    CHAT: "/api/chat",
    DOCUMENTS: "/api/documents",
    DOCUMENTS_UPLOAD: "/api/documents/upload",
    DOCUMENTS_REINDEX: (id) => `/api/documents/${id}/reindex`,
    DOCUMENTS_DELETE: (id) => `/api/documents/${id}`,
    DOCUMENTS_DETAIL: (id) => `/api/documents/${id}`,
    ADMIN_STATS: "/api/admin/stats",
    ADMIN_EVALUATION: "/api/admin/evaluation",
  },
  POLL_INTERVAL_MS: 15000,
};

window.CONFIG = CONFIG;
