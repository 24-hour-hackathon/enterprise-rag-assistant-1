\# Enterprise RAG Assistant



\## JP-020 — Programming Language: Java/Python with AI/ML



An enterprise document question-answering system that allows users to ask natural-language questions about an approved collection of enterprise documents and receive concise, document-grounded answers with source references.



\## Problem



Enterprise information is often distributed across policies, SOPs, manuals, and process documents. Searching these documents manually is slow and can lead to answers that are not properly supported by the source material.



This project provides a Retrieval-Augmented Generation (RAG) assistant that retrieves relevant document content before generating an answer.



\## Solution



The system:



1\. Accepts enterprise documents in PDF, DOCX, and TXT formats.

2\. Extracts and cleans document text.

3\. Splits documents into meaningful chunks.

4\. Generates semantic embeddings.

5\. Stores embeddings in ChromaDB.

6\. Retrieves the most relevant chunks for a user's question.

7\. Uses an LLM to generate a concise answer using only retrieved context.

8\. Provides document and page/section references.

9\. Refuses unsupported questions when relevant information is not available.

10\. Supports document re-indexing and deletion.



\## Architecture



```text

&#x20;                ┌─────────────────────┐

&#x20;                │      User Query     │

&#x20;                └──────────┬──────────┘

&#x20;                           │

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │    FastAPI Backend  │

&#x20;                └──────────┬──────────┘

&#x20;                           │

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │ Query Embedding     │

&#x20;                │ Sentence Transformer│

&#x20;                └──────────┬──────────┘

&#x20;                           │

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │      ChromaDB       │

&#x20;                │ Semantic Retrieval  │

&#x20;                └──────────┬──────────┘

&#x20;                           │

&#x20;                   Relevant Chunks

&#x20;                           │

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │    Gemini LLM       │

&#x20;                │ Grounded Generation │

&#x20;                └──────────┬──────────┘

&#x20;                           │

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │ Answer + Citations  │

&#x20;                └─────────────────────┘

Technology Stack

Backend

Python

FastAPI

Uvicorn

Pydantic

SQLAlchemy

SQLite

RAG / AI

Sentence Transformers

all-MiniLM-L6-v2

ChromaDB

Google Gemini

google-genai

Document Processing

PyMuPDF

python-docx

TXT parsing

Frontend

HTML

CSS

JavaScript

RAG Pipeline

1\. Ingestion



Documents are uploaded through the document management API.



2\. Parsing



PDF, DOCX, and TXT files are converted into text while preserving useful metadata such as page and section information.



3\. Chunking



Documents are divided into manageable overlapping chunks while attempting to preserve paragraph boundaries.



4\. Embedding



Each chunk is converted into a vector representation using:



sentence-transformers/all-MiniLM-L6-v2



5\. Vector Storage



Embeddings and metadata are stored in ChromaDB.



6\. Retrieval



The user's question is embedded and semantically compared with stored document chunks.



7\. Grounded Generation



Relevant chunks are supplied to the language model as context. The system is instructed to answer using the approved knowledge base.



8\. Citation



The response includes the source document and available page/section metadata.



9\. Unsupported Questions



If relevant information cannot be retrieved, the system returns an information-not-available response rather than fabricating an answer.



Supported Documents

PDF

DOCX

TXT

API

Health



GET /health



Checks backend and AI configuration status.



Chat



POST /api/chat



Accepts a natural-language question and returns a grounded response with source information.



Documents



GET /api/documents



Lists indexed documents.



POST /api/documents/upload



Uploads and indexes a document.



POST /api/documents/{id}/reindex



Re-indexes an existing document.



DELETE /api/documents/{id}



Deletes a document from the knowledge base.



Evaluation



GET /api/evaluation/results



Returns evaluation results.



POST /api/evaluation/run



Runs the evaluation pipeline.



Running the Backend



From the project root:



cd backend

pip install -r requirements.txt



Configure environment variables using .env.



Start the API:



uvicorn app.main:app --reload --app-dir backend



API documentation:



http://127.0.0.1:8000/docs



Health:



http://127.0.0.1:8000/health



Running the Frontend



The integrated frontend can be served locally using:



cd frontend

python -m http.server 3000



Then open:



http://127.0.0.1:3000



Testing



The backend automated test suite currently passes:



27 passed

3 warnings



Testing covers:



Health API

Chat API

Document upload

Document deletion

Re-indexing

Chunking

Embeddings

Retrieval

Vector store

RAG pipeline

Gemini provider integration

File parsing

Evaluation functionality

Evaluation



The evaluation framework contains 26 test cases covering:



Direct questions

Semantic/paraphrased questions

Unsupported questions

Out-of-domain questions

Source citation

Empty/invalid input

Re-index consistency



The evaluation system also includes rate-limit handling for external LLM APIs.



Security



API keys are stored in local .env files and are excluded from Git using .gitignore.



.env.example files are provided as configuration templates.



Never commit real API keys or other secrets.

AI Disclosure



AI tools were used during development for:



Code generation and implementation assistance

Debugging

Test generation

RAG pipeline development

Documentation assistance

Frontend integration assistance



The team reviewed, tested, and integrated the generated code into the final application.



The application's RAG pipeline, document retrieval, grounding logic, evaluation framework, API integration, and user interface were tested as part of the development process.



Team Contributions

Pavi



Frontend development and UX.



YDK



Evaluation, integration, and testing.



Sashi



Evaluation, integration, testing, and edge-case validation.



NSH



Backend, RAG pipeline, AI/LLM integration, database, document ingestion, and administration functionality.



Project Goal



The goal is to provide a reliable enterprise knowledge assistant that answers questions using approved organizational documents while minimizing unsupported or hallucinated responses.

