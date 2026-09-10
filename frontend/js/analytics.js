// Analytics & Evaluation Controller Module
const AnalyticsView = {
  elements: {},

  init() {
    this.elements = {
      totalDocs: document.getElementById("metric-total-docs"),
      totalChunks: document.getElementById("metric-total-chunks"),
      totalQuestions: document.getElementById("metric-total-questions"),
      groundedRate: document.getElementById("metric-grounded-rate"),
      avgLatency: document.getElementById("metric-avg-latency"),
      refreshBtn: document.getElementById("analytics-refresh-btn"),
      evalTableBody: document.getElementById("eval-table-body"),
    };

    this.bindEvents();
    this.loadMetrics();
  },

  bindEvents() {
    if (this.elements.refreshBtn) {
      this.elements.refreshBtn.addEventListener("click", () => {
        this.loadMetrics();
        App.showToast("Metrics refreshed", "info");
      });
    }
  },

  async loadMetrics() {
    try {
      const [stats, evalData] = await Promise.all([
        API.getAdminStats().catch(() => ({})),
        API.getEvaluation().catch(() => ({})),
      ]);

      this.renderKPIs(stats, evalData);
      this.renderEvaluations(evalData);
    } catch (err) {
      console.error("Error loading analytics metrics:", err);
    }
  },

  renderKPIs(stats = {}, evalData = {}) {
    if (this.elements.totalDocs) {
      this.elements.totalDocs.textContent = stats.total_documents ?? 0;
    }
    if (this.elements.totalChunks) {
      this.elements.totalChunks.textContent = stats.total_chunks ?? 0;
    }
    if (this.elements.totalQuestions) {
      this.elements.totalQuestions.textContent = stats.total_questions ?? 0;
    }
    if (this.elements.groundedRate) {
      const rate = evalData.grounded_rate_percentage ?? 100;
      this.elements.groundedRate.textContent = `${rate}%`;
    }
    if (this.elements.avgLatency) {
      const lat = evalData.average_latency_ms ?? 0;
      this.elements.avgLatency.textContent = `${lat} ms`;
    }
  },

  renderEvaluations(evalData = {}) {
    if (!this.elements.evalTableBody) return;

    const items = evalData.recent_evaluations || [];
    if (items.length === 0) {
      this.elements.evalTableBody.innerHTML = `
        <tr>
          <td colspan="4" class="table-empty">
            No query evaluations logged yet. Ask questions in the Assistant tab to generate audit metrics.
          </td>
        </tr>
      `;
      return;
    }

    this.elements.evalTableBody.innerHTML = items.map((item) => {
      const statusBadge = item.is_grounded
        ? `<span class="badge badge-success">✓ Grounded</span>`
        : `<span class="badge badge-warning">⚠ Unsupported</span>`;

      const dateStr = new Date(item.created_at).toLocaleTimeString();
      const latencyStr = item.latency_ms ? `${item.latency_ms} ms` : "N/A";

      return `
        <tr>
          <td style="font-weight:600;">${this.escapeHtml(item.question)}</td>
          <td>${statusBadge}</td>
          <td><span style="font-family:var(--font-mono); font-size:0.85rem; color:var(--accent-cyan);">${latencyStr}</span></td>
          <td style="font-size:0.82rem; color:var(--text-secondary);">${dateStr}</td>
        </tr>
      `;
    }).join("");
  },

  escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  },
};

window.AnalyticsView = AnalyticsView;
