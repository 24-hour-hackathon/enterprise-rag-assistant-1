// Main Application Coordinator
const App = {
  activeTab: "chat",

  init() {
    this.setupNavigation();
    this.checkHealth();

    // Initialize sub-views
    if (window.ChatView) ChatView.init();
    if (window.DocumentsView) DocumentsView.init();
    if (window.AnalyticsView) AnalyticsView.init();

    // Polling backend health periodically
    setInterval(() => this.checkHealth(), CONFIG.POLL_INTERVAL_MS);
  },

  setupNavigation() {
    const tabButtons = document.querySelectorAll(".nav-tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");
        if (!targetTab) return;

        this.activeTab = targetTab;

        // Update active tab buttons
        tabButtons.forEach((b) => b.classList.toggle("active", b === btn));

        // Update active tab contents
        tabContents.forEach((tc) => {
          tc.classList.toggle("active", tc.id === `tab-${targetTab}`);
        });

        // Trigger view-specific refreshes
        if (targetTab === "documents" && window.DocumentsView) {
          DocumentsView.loadDocuments();
        } else if (targetTab === "analytics" && window.AnalyticsView) {
          AnalyticsView.loadMetrics();
        }
      });
    });
  },

  async checkHealth() {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");

    try {
      const data = await API.checkHealth();
      if (dot) {
        dot.className = "status-dot online";
      }
      if (text) {
        text.textContent = `Backend Online (${data.llm_provider || 'RAG'})`;
      }
    } catch (err) {
      if (dot) {
        dot.className = "status-dot offline";
      }
      if (text) {
        text.textContent = "Backend Offline (Disconnected)";
      }
    }
  },

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "❌";

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(30px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },
};

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});

window.App = App;
