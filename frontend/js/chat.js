// Chat Controller Module
const ChatView = {
  elements: {},
  isSubmitting: false,

  init() {
    this.elements = {
      container: document.getElementById("chat-messages"),
      emptyState: document.getElementById("chat-empty-state"),
      form: document.getElementById("chat-form"),
      textarea: document.getElementById("chat-input"),
      sendBtn: document.getElementById("chat-send-btn"),
      clearBtn: document.getElementById("chat-clear-btn"),
      suggestions: document.querySelectorAll(".suggestion-btn"),
    };

    this.bindEvents();
  },

  bindEvents() {
    // Form submit
    if (this.elements.form) {
      this.elements.form.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleSubmit();
      });
    }

    // Auto-expand textarea & Enter to submit (Shift+Enter for newline)
    if (this.elements.textarea) {
      this.elements.textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.handleSubmit();
        }
      });

      this.elements.textarea.addEventListener("input", () => {
        this.elements.textarea.style.height = "auto";
        this.elements.textarea.style.height = `${Math.min(this.elements.textarea.scrollHeight, 140)}px`;
      });
    }

    // Suggestion pills
    if (this.elements.suggestions) {
      this.elements.suggestions.forEach((btn) => {
        btn.addEventListener("click", () => {
          const query = btn.getAttribute("data-query");
          if (query && this.elements.textarea) {
            this.elements.textarea.value = query;
            this.handleSubmit();
          }
        });
      });
    }

    // Clear chat
    if (this.elements.clearBtn) {
      this.elements.clearBtn.addEventListener("click", () => {
        this.clearMessages();
      });
    }
  },

  clearMessages() {
    if (this.elements.container) {
      this.elements.container.innerHTML = "";
      if (this.elements.emptyState) {
        this.elements.container.appendChild(this.elements.emptyState);
        this.elements.emptyState.style.display = "flex";
      }
    }
  },

  async handleSubmit() {
    if (this.isSubmitting) return;

    const question = this.elements.textarea.value.trim();
    if (!question) return;

    // Reset input
    this.elements.textarea.value = "";
    this.elements.textarea.style.height = "52px";

    // Hide empty state
    if (this.elements.emptyState) {
      this.elements.emptyState.style.display = "none";
    }

    // Append user message
    this.appendUserMessage(question);

    // Show typing indicator
    const typingElement = this.appendTypingIndicator();
    this.scrollToBottom();

    // Lock submit
    this.setLoading(true);

    try {
      const response = await API.askQuestion(question);
      // Remove typing indicator
      typingElement.remove();
      // Render assistant answer
      this.appendAssistantResponse(response);
    } catch (err) {
      typingElement.remove();
      this.appendErrorResponse(err.message || "Failed to generate answer. Please check if backend is running.");
      App.showToast(err.message || "Request failed", "error");
    } finally {
      this.setLoading(false);
      this.scrollToBottom();
    }
  },

  appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-turn";
    row.innerHTML = `
      <div class="user-message-row">
        <div class="user-bubble">${this.escapeHtml(text)}</div>
      </div>
    `;
    this.elements.container.appendChild(row);
  },

  appendTypingIndicator() {
    const row = document.createElement("div");
    row.className = "message-turn typing-turn";
    row.innerHTML = `
      <div class="assistant-message-row">
        <div class="assistant-avatar">🤖</div>
        <div class="assistant-card">
          <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
      </div>
    `;
    this.elements.container.appendChild(row);
    return row;
  },

  appendAssistantResponse(data) {
    const { answer, has_answer, sources = [] } = data;
    const row = document.createElement("div");
    row.className = "message-turn";

    let statusBadge = "";
    let contentHtml = "";

    if (has_answer) {
      statusBadge = `<span class="badge badge-success">✓ Grounded Answer</span>`;
      contentHtml = `<div class="answer-text">${this.escapeHtml(answer)}</div>`;
    } else {
      statusBadge = `<span class="badge badge-warning">⚠ Information Not in KB</span>`;
      contentHtml = `
        <div class="unsupported-banner">
          <span class="icon">ℹ️</span>
          <div>
            <strong>Strict Grounding Notice:</strong><br/>
            ${this.escapeHtml(answer)}
          </div>
        </div>
      `;
    }

    // Source Citations
    let citationsHtml = "";
    if (sources && sources.length > 0) {
      const sourceCards = sources.map((src, idx) => {
        const docName = this.escapeHtml(src.document || "Document");
        const pageNum = src.page ? `Page ${src.page}` : "Page 1";
        const section = src.section ? this.escapeHtml(src.section) : "General";
        const excerpt = this.escapeHtml(src.supporting_text || "");
        const score = src.relevance_score ? `${Math.round(src.relevance_score * 100)}% match` : "";

        return `
          <div class="citation-card">
            <div class="citation-top-row">
              <div class="citation-doc-info">
                📄 <span>${docName}</span>
                <span class="citation-meta-pill">${pageNum}</span>
                <span class="citation-meta-pill">${section}</span>
              </div>
              ${score ? `<span class="citation-score">${score}</span>` : ""}
            </div>
            <div class="citation-excerpt">"${excerpt}"</div>
          </div>
        `;
      }).join("");

      citationsHtml = `
        <div class="citations-section">
          <div class="citations-header">
            📑 Supporting Source References (${sources.length})
          </div>
          <div class="citations-grid">
            ${sourceCards}
          </div>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="assistant-message-row">
        <div class="assistant-avatar">🤖</div>
        <div class="assistant-card">
          <div class="assistant-header">
            <div class="grounding-status">${statusBadge}</div>
            <span style="font-size:0.75rem; color:var(--text-muted);">Enterprise AI</span>
          </div>
          ${contentHtml}
          ${citationsHtml}
        </div>
      </div>
    `;

    this.elements.container.appendChild(row);
  },

  appendErrorResponse(errorMessage) {
    const row = document.createElement("div");
    row.className = "message-turn";
    row.innerHTML = `
      <div class="assistant-message-row">
        <div class="assistant-avatar" style="background:var(--danger-bg); color:var(--danger); border-color:var(--danger-border);">⚠️</div>
        <div class="assistant-card" style="border-color:var(--danger-border);">
          <div class="assistant-header">
            <span class="badge badge-danger">Connection / System Error</span>
          </div>
          <div class="answer-text" style="color:#fca5a5;">${this.escapeHtml(errorMessage)}</div>
        </div>
      </div>
    `;
    this.elements.container.appendChild(row);
  },

  setLoading(loading) {
    this.isSubmitting = loading;
    if (this.elements.sendBtn) {
      this.elements.sendBtn.disabled = loading;
      this.elements.sendBtn.innerHTML = loading
        ? `<span>Processing...</span>`
        : `<span>Ask Assistant</span> <span style="font-size:1.1rem;">↗</span>`;
    }
    if (this.elements.textarea) {
      this.elements.textarea.disabled = loading;
    }
  },

  scrollToBottom() {
    if (this.elements.container) {
      this.elements.container.scrollTop = this.elements.container.scrollHeight;
    }
  },

  escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  },
};

window.ChatView = ChatView;
