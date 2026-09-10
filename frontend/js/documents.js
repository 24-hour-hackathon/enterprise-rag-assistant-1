// Document Management Controller Module
const DocumentsView = {
  elements: {},
  documents: [],

  init() {
    this.elements = {
      dropzone: document.getElementById("upload-dropzone"),
      fileInput: document.getElementById("file-input"),
      progressWrapper: document.getElementById("upload-progress"),
      progressFill: document.getElementById("upload-progress-fill"),
      progressText: document.getElementById("upload-progress-text"),
      tableBody: document.getElementById("doc-table-body"),
      searchInput: document.getElementById("doc-search-input"),
      refreshBtn: document.getElementById("doc-refresh-btn"),
      totalCountBadge: document.getElementById("doc-total-badge"),
    };

    this.bindEvents();
    this.loadDocuments();
  },

  bindEvents() {
    // File dropzone click
    if (this.elements.dropzone && this.elements.fileInput) {
      this.elements.dropzone.addEventListener("click", () => {
        this.elements.fileInput.click();
      });

      this.elements.fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
          this.handleFileUpload(e.target.files[0]);
        }
      });

      // Drag and drop events
      ["dragenter", "dragover"].forEach((eventName) => {
        this.elements.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.elements.dropzone.classList.add("dragover");
        });
      });

      ["dragleave", "drop"].forEach((eventName) => {
        this.elements.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.elements.dropzone.classList.remove("dragover");
        });
      });

      this.elements.dropzone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleFileUpload(e.dataTransfer.files[0]);
        }
      });
    }

    // Refresh button
    if (this.elements.refreshBtn) {
      this.elements.refreshBtn.addEventListener("click", () => {
        this.loadDocuments();
      });
    }

    // Search filter
    if (this.elements.searchInput) {
      this.elements.searchInput.addEventListener("input", (e) => {
        this.filterTable(e.target.value);
      });
    }
  },

  async loadDocuments() {
    try {
      if (this.elements.tableBody) {
        this.elements.tableBody.innerHTML = `
          <tr>
            <td colspan="6" class="table-empty">Loading documents from knowledge base...</td>
          </tr>
        `;
      }

      const res = await API.getDocuments();
      this.documents = res.documents || [];
      this.renderTable(this.documents);

      if (this.elements.totalCountBadge) {
        this.elements.totalCountBadge.textContent = `${this.documents.length} Docs`;
      }
    } catch (err) {
      console.error("Error loading documents:", err);
      if (this.elements.tableBody) {
        this.elements.tableBody.innerHTML = `
          <tr>
            <td colspan="6" class="table-empty" style="color:#f87171;">
              Failed to load documents: ${this.escapeHtml(err.message)}
            </td>
          </tr>
        `;
      }
    }
  },

  renderTable(docs) {
    if (!this.elements.tableBody) return;

    if (!docs || docs.length === 0) {
      this.elements.tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="table-empty">
            No enterprise documents indexed yet. Upload a PDF, DOCX, or TXT document above.
          </td>
        </tr>
      `;
      return;
    }

    this.elements.tableBody.innerHTML = docs.map((doc) => {
      const typeClass = `doc-type-${(doc.file_type || 'txt').toLowerCase()}`;
      const statusBadge = this.getStatusBadge(doc.status);
      const createdDate = new Date(doc.created_at).toLocaleString();

      return `
        <tr data-id="${doc.id}">
          <td>
            <div class="doc-file-info">
              <div class="doc-type-icon ${typeClass}">${(doc.file_type || 'txt').toUpperCase()}</div>
              <div>
                <div class="doc-name">${this.escapeHtml(doc.filename)}</div>
                <div class="doc-id-sub">ID: ${doc.id.substring(0, 8)}...</div>
              </div>
            </div>
          </td>
          <td>${statusBadge}</td>
          <td>
            <span class="badge badge-info">v${doc.version}</span>
          </td>
          <td>
            <strong style="color:var(--text-primary);">${doc.chunk_count}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">chunks</span>
          </td>
          <td style="font-size:0.82rem; color:var(--text-secondary);">${createdDate}</td>
          <td>
            <div class="table-actions">
              <button 
                class="btn btn-secondary btn-icon" 
                title="Re-index Document"
                onclick="DocumentsView.handleReindex('${doc.id}', '${this.escapeHtml(doc.filename)}')"
              >
                🔄
              </button>
              <button 
                class="btn btn-danger btn-icon" 
                title="Delete Document"
                onclick="DocumentsView.handleDelete('${doc.id}', '${this.escapeHtml(doc.filename)}')"
              >
                🗑️
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  },

  getStatusBadge(status) {
    const s = (status || "PENDING").toUpperCase();
    if (s === "INDEXED") {
      return `<span class="badge badge-success">● Indexed</span>`;
    } else if (s === "FAILED") {
      return `<span class="badge badge-danger">● Failed</span>`;
    }
    return `<span class="badge badge-warning">● Pending</span>`;
  },

  filterTable(query) {
    const q = (query || "").toLowerCase().trim();
    if (!q) {
      this.renderTable(this.documents);
      return;
    }

    const filtered = this.documents.filter((d) =>
      d.filename.toLowerCase().includes(q) ||
      d.id.toLowerCase().includes(q) ||
      (d.file_type || "").toLowerCase().includes(q)
    );

    this.renderTable(filtered);
  },

  async handleFileUpload(file) {
    if (!file) return;

    // Validate extension
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx", "txt", "doc"].includes(ext)) {
      App.showToast("Unsupported file format. Please upload PDF, DOCX, or TXT.", "error");
      return;
    }

    // Show progress
    this.showProgress(true, `Uploading and indexing '${file.name}'...`, 40);

    try {
      const response = await API.uploadDocument(file);
      this.showProgress(true, `Indexing completed (${response.chunk_count} chunks)`, 100);

      App.showToast(`'${file.name}' indexed successfully!`, "success");
      setTimeout(() => {
        this.showProgress(false);
        this.loadDocuments();
      }, 1000);
    } catch (err) {
      this.showProgress(false);
      App.showToast(`Upload failed: ${err.message}`, "error");
    } finally {
      if (this.elements.fileInput) {
        this.elements.fileInput.value = "";
      }
    }
  },

  async handleReindex(id, filename) {
    if (!confirm(`Re-index document '${filename}'? This will purge old vectors, regenerate embeddings, and increment version.`)) {
      return;
    }

    try {
      App.showToast(`Re-indexing '${filename}'...`, "info");
      const res = await API.reindexDocument(id);
      App.showToast(`Document re-indexed to version ${res.version} with ${res.chunk_count} chunks!`, "success");
      this.loadDocuments();
    } catch (err) {
      App.showToast(`Re-indexing failed: ${err.message}`, "error");
    }
  },

  async handleDelete(id, filename) {
    if (!confirm(`Delete document '${filename}' and its vector embeddings? This action cannot be undone.`)) {
      return;
    }

    try {
      await API.deleteDocument(id);
      App.showToast(`Document '${filename}' deleted successfully`, "success");
      this.loadDocuments();
    } catch (err) {
      App.showToast(`Delete failed: ${err.message}`, "error");
    }
  },

  showProgress(show, text = "", percent = 0) {
    if (!this.elements.progressWrapper) return;
    this.elements.progressWrapper.style.display = show ? "block" : "none";
    if (this.elements.progressFill) this.elements.progressFill.style.width = `${percent}%`;
    if (this.elements.progressText) this.elements.progressText.textContent = text;
  },

  escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  },
};

window.DocumentsView = DocumentsView;
