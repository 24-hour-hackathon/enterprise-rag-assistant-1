# Enterprise Document QA Assistant - Frontend

A modern, responsive, and enterprise-grade web interface for **Problem Statement JP-020: Enterprise Document Question-Answering Assistant with RAG**.

---

## 🌟 Key Features

1. **AI Chat Assistant**:
   - Natural-language query input with quick-start prompts.
   - Grounded responses with **✓ Grounded Answer** verification badges.
   - Expandable **Source Reference Cards** displaying Document Name, Page Number, Section Title, Relevance Score, and exact text excerpts.
   - Distinct **Unsupported Query Notice** for ungrounded or out-of-domain questions with zero hallucination.

2. **Enterprise Document Management**:
   - Drag-and-drop file upload for `.pdf`, `.docx`, and `.txt` files up to 25MB.
   - Real-time indexing progress bar.
   - Comprehensive documents table with status badges (`INDEXED`, `PENDING`, `FAILED`), versioning, and chunk counts.
   - **One-click Re-Indexing** (`POST /api/documents/{id}/reindex`) and **Deletion** (`DELETE /api/documents/{id}`).

3. **RAG Evaluation & Analytics Dashboard**:
   - Real-time KPIs for Total Documents, Vector Chunks, Total Questions, Grounding Pass Rate %, and Average Latency (ms).
   - Recent query audit logs and evaluation breakdown.

4. **Live System Telemetry**:
   - Persistent header badge indicating live backend connectivity and active LLM provider.

---

## 🚀 How to Run

### 1. Ensure Backend is Running
In one terminal:
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```
Backend will be live at `http://127.0.0.1:8000`.

### 2. Launch the Frontend
You can open `frontend/index.html` directly in any web browser, or serve it using any lightweight static web server:

**Option A: Python HTTP Server (Recommended)**
```powershell
cd frontend
python -m http.server 3000
```
Then visit: [http://localhost:3000](http://localhost:3000)

**Option B: Direct Browser Open**
Double-click `frontend/index.html` or open in Chrome / Edge / Firefox.

---

## 📁 Project Structure

```
frontend/
├── index.html                   # Main single-page web app
├── css/
│   ├── variables.css            # Enterprise design tokens & themes
│   ├── base.css                 # Layout, header, tabs, and glass cards
│   ├── chat.css                 # Q&A conversation, bubbles & citation cards
│   ├── documents.css            # Dropzone, upload progress & doc table
│   └── analytics.css            # KPI cards & evaluation telemetry
├── js/
│   ├── config.js                # API endpoints and base URL
│   ├── api.js                   # Fetch API client wrapper
│   ├── chat.js                  # Chat controller & citation rendering
│   ├── documents.js             # Document list, upload, reindex & delete
│   ├── analytics.js             # Metrics calculation & evaluation logs
│   └── app.js                   # App coordinator, tab router & toast alerts
└── README.md
```
