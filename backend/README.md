# Enterprise Document Question-Answering Assistant with RAG

A production-ready, modular, and testable FastAPI backend for **Problem Statement JP-020: Enterprise Document Question-Answering Assistant with RAG**.

The system enables enterprise users to ask natural-language questions over verified documents (PDF, DOCX, TXT) and returns concise, document-grounded answers backed by explicit source citations, strictly avoiding ungrounded hallucinations.

---

## 🌟 Key Features

- **Multi-Format Ingestion**: Ingests PDF (`PyMuPDF`), DOCX (`python-docx`), and TXT documents while preserving document structures, page numbers, and section headers.
- **Paragraph-Aware Chunking**: Chunks text at 500–800 words with 100-word overlap, respecting natural paragraph boundaries.
- **Local Dense Embeddings**: Generates semantic embeddings with `sentence-transformers/all-MiniLM-L6-v2`.
- **Persistent Vector Store**: Persistent local vector indexing using **ChromaDB**.
- **Relevance-Grounded Retrieval**: Computes similarity scores and rejects low-confidence chunks before prompt synthesis.
- **Multi-Provider LLM Abstraction**: Supports OpenAI (`gpt-4o-mini`), Google Gemini (`gemini-1.5-flash`), Anthropic (`claude-3-haiku`), and a deterministic `Mock` provider for testing/offline environments.
- **Auditing & Admin Analytics**: SQLite + SQLAlchemy logging for queries, sources, document versions, and RAG evaluation metrics.

---

## 📁 Project Architecture

```
backend/
├── app/
│   ├── main.py                     # FastAPI entrypoint, CORS, lifespan
│   ├── api/
│   │   ├── documents.py            # Upload, list, detail, reindex, delete
│   │   ├── chat.py                 # Grounded Q&A chat endpoint
│   │   └── admin.py                # Analytics & evaluation stats
│   ├── core/
│   │   ├── config.py               # Pydantic Settings & environment variables
│   │   └── database.py             # SQLite engine & session management
│   ├── models/
│   │   ├── document.py             # Document SQL model
│   │   ├── query.py                # Query & Source citation SQL models
│   │   └── evaluation.py          # Evaluation metrics model
│   ├── schemas/
│   │   ├── document.py             # Document Pydantic schemas
│   │   ├── chat.py                 # Chat & SourceReference schemas
│   │   └── admin.py                # Admin stats & evaluation schemas
│   ├── services/
│   │   ├── ingestion.py            # Upload validation, text extraction & DB sync
│   │   ├── chunking.py             # Paragraph-aware chunking service
│   │   ├── embeddings.py           # SentenceTransformer singleton wrapper
│   │   ├── vector_store.py         # ChromaDB client & collection management
│   │   ├── retrieval.py            # Top-K search & relevance threshold filter
│   │   ├── rag.py                  # Grounding verification & prompt construction
│   │   └── llm.py                  # Multi-provider LLM adapter
│   └── utils/
│       └── file_parser.py          # PyMuPDF, python-docx, and TXT parser
├── data/
│   ├── uploads/                    # Staged enterprise documents
│   └── chroma/                     # Persistent ChromaDB vector data
├── tests/                          # 100% passing test suite
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11, 3.12, 3.14)
- `pip`

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` to configure your preferred LLM provider:
```ini
LLM_PROVIDER="mock"            # Options: "mock", "openai", "gemini", "anthropic"
LLM_API_KEY=""                # Add API key if using openai / gemini / anthropic
LLM_MODEL="gpt-4o-mini"
```

---

## 🏃 Running the Application

Start the FastAPI server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Automated Tests

Run the test suite with `pytest`:

```bash
pytest tests/ -v
```

The test suite covers:
- Health check endpoints
- PDF, DOCX, and TXT document parsing
- Paragraph-aware chunking and overlap verification
- 384-dimensional dense embeddings
- ChromaDB vector CRUD operations
- Semantic retrieval with relevance threshold rejection
- Supported questions returning citations
- Unsupported out-of-domain questions returning fallback responses
- Document lifecycle (upload, reindex, delete)
- Admin analytics and evaluation metrics

---

## 📡 API Reference & Sample cURL Requests

### 1. Upload & Index Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Leave_Policy.pdf"
```

**Response (201 Created):**
```json
{
  "id": "e81d7f1c-7b44-469b-83ee-c01375d861f2",
  "filename": "Leave_Policy.pdf",
  "status": "INDEXED",
  "version": 1,
  "chunk_count": 5,
  "message": "Document successfully uploaded and indexed."
}
```

### 2. Ask a Grounded Question (RAG Chat)
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the annual leave allowance?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "All full-time employees are entitled to 20 days of paid annual leave per calendar year.",
  "has_answer": true,
  "sources": [
    {
      "document": "Leave_Policy.pdf",
      "document_id": "e81d7f1c-7b44-469b-83ee-c01375d861f2",
      "page": 2,
      "section": "Annual Leave Entitlement",
      "chunk_id": "doc_e81d7f1c_chunk_3a91b402",
      "supporting_text": "Employees receive 20 days of paid annual leave...",
      "relevance_score": 0.8842
    }
  ],
  "query_id": "1894d03e-5f11-477a-b9c1-4ca690184451"
}
```

### 3. Unsupported Question Handling
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the recipe for chocolate chip cookies?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "I couldn't find sufficient information in the approved knowledge base to answer this question.",
  "has_answer": false,
  "sources": [],
  "query_id": "bf310b89-20f5-460d-963a-bbff22119ef2"
}
```

### 4. Admin Knowledge Base Statistics
```bash
curl -X GET "http://localhost:8000/api/admin/stats"
```

**Response (200 OK):**
```json
{
  "total_documents": 12,
  "indexed_documents": 12,
  "failed_documents": 0,
  "total_chunks": 84,
  "total_questions": 150,
  "total_answered_questions": 142
}
```

---

## 🔒 Security & Grounding Policy

- **Strict Context Prompting**: The system explicitly forbids the LLM from utilizing external pre-trained knowledge or guessing missing details.
- **Relevance Gate**: Any vector candidate scoring below the similarity threshold is rejected before reaching the LLM prompt.
- **No Path Traversal**: Uploaded filenames are sanitized and stored using UUID namespaces.
- **Clean Document Lifecycle**: Deleting or re-indexing a document atomically purges its vector embeddings from ChromaDB.
