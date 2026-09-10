// API Client Module
const API = {
  /**
   * General request wrapper with error handling.
   */
  async request(endpoint, options = {}) {
    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    const defaultHeaders = {};

    if (!(options.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }
    defaultHeaders["Accept"] = "application/json";

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMessage = data.detail || data.message || `Request failed with status ${response.status}`;
        throw new Error(errorMessage);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
      throw err;
    }
  },

  // Health Check
  async checkHealth() {
    return this.request(CONFIG.ENDPOINTS.HEALTH);
  },

  // Chat Q&A
  async askQuestion(question, topK = null) {
    const payload = { question };
    if (topK) payload.top_k = topK;

    return this.request(CONFIG.ENDPOINTS.CHAT, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Document Management
  async getDocuments() {
    return this.request(CONFIG.ENDPOINTS.DOCUMENTS);
  },

  async getDocument(id) {
    return this.request(CONFIG.ENDPOINTS.DOCUMENTS_DETAIL(id));
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    return this.request(CONFIG.ENDPOINTS.DOCUMENTS_UPLOAD, {
      method: "POST",
      body: formData,
    });
  },

  async reindexDocument(id) {
    return this.request(CONFIG.ENDPOINTS.DOCUMENTS_REINDEX(id), {
      method: "POST",
    });
  },

  async deleteDocument(id) {
    return this.request(CONFIG.ENDPOINTS.DOCUMENTS_DELETE(id), {
      method: "DELETE",
    });
  },

  // Admin & Evaluation
  async getAdminStats() {
    return this.request(CONFIG.ENDPOINTS.ADMIN_STATS);
  },

  async getEvaluation() {
    return this.request(CONFIG.ENDPOINTS.ADMIN_EVALUATION);
  },
};

window.API = API;
