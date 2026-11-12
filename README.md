# Agentic RAG Assistant

A document-grounded AI research assistant that uses Retrieval-Augmented Generation (RAG) to answer natural-language questions from indexed documents, with source citations and supporting references.

**[Live Demo](https://agentic-rag-assistant-web.vercel.app/)** · **[GitHub Repository](https://github.com/Sherry2005/agentic-rag-assistant)**

## Overview

Agentic RAG Assistant is a full-stack AI application designed to make information retrieval from technical documents more accessible and reliable.

Instead of relying exclusively on an LLM's pretrained knowledge, the system retrieves relevant passages from a document knowledge base and uses them as context for generating answers.

The current knowledge base focuses on renewable energy policies, federal renewable energy programs, and Solar Renewable Energy Certificate (SREC) markets.

The assistant returns answers with numbered citations and source metadata, including document titles, page numbers, and sections, allowing users to trace information back to its original source.

## Features

- **PDF and HTML ingestion:** Extracts and processes content from different document formats.
- **Intelligent document chunking:** Splits documents into searchable passages while preserving relevant structural information.
- **Table-aware PDF processing:** Preserves complete tables as individual chunks instead of fragmenting their contents.
- **Semantic search:** Uses vector embeddings to retrieve relevant document passages based on meaning.
- **Vector database:** Stores document embeddings and metadata in PostgreSQL with pgvector.
- **Grounded answer generation:** Uses an LLM to generate responses based on retrieved document content.
- **Source citations:** Provides numbered references with document, page, and section information.
- **Context-aware responses:** Instructs the assistant to acknowledge insufficient information rather than invent unsupported answers.
- **REST API:** Exposes the assistant through a FastAPI backend.
- **Web interface:** Provides a Next.js frontend for interacting with the assistant.

## Architecture

The application follows a retrieval-augmented generation pipeline:

```text
                 User Question
                       |
                       v
                 Next.js Frontend
                       |
                       v
                  FastAPI Backend
                       |
                       v
               Query Embedding
                       |
                       v
              FastEmbed Model
                       |
                       v
             PostgreSQL + pgvector
                       |
                       v
              Semantic Retrieval
                       |
                       v
              Relevant Text Chunks
                       |
                       v
                  Groq LLM
                       |
                       v
             Grounded Answer
                       |
                       v
             Citations + Sources
                       |
                       v
                 Web Interface
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| LLM Provider | Groq |
| Language Model | openai/gpt-oss-120b |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| Embedding Framework | FastEmbed |
| Vector Database | PostgreSQL + pgvector |
| Backend API | FastAPI |
| Frontend | Next.js, React, TypeScript |
| Styling | Tailwind CSS |
| Document Processing | BeautifulSoup, PyPDF, Poppler |
| Database Connectivity | Psycopg |

## Project Structure

```text
agentic-rag-assistant/
│
├── api/
│   └── main.py
│
├── eval/
│   └── golden.jsonl
│
├── frontend/
│   ├── app/
│   └── package.json
│
├── src/
│   └── ingest/
│       ├── ingest_pdf.py
│       ├── ingest_to_db.py
│       ├── read_html.py
│       └── chunk_text.py
│
├── ask_assistant.py
├── schema.sql
├── requirements.txt
├── test_db.py
├── test_ingestion.py
├── test_retrieval.py
└── verify_db.py
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Sherry2005/agentic-rag-assistant.git

cd agentic-rag-assistant
```

### 2. Set up the Python environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

For PDF processing, also install `pypdf` and Poppler (`pdftotext`).

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=your_postgresql_connection_string
GROQ_API_KEY=your_groq_api_key
FRONTEND_URL=http://localhost:3000
```

- `DATABASE_URL`: PostgreSQL connection string for the database.
- `GROQ_API_KEY`: API key for accessing the Groq inference service.
- `FRONTEND_URL`: Frontend origin used for backend CORS configuration.

Never commit API keys or database credentials to GitHub.

### 4. Initialize the database

The project uses PostgreSQL with the pgvector extension.

Execute the SQL statements in `schema.sql` against your database. This creates the document and document-chunk tables, enables vector support, and creates the relevant indexes.

### 5. Ingest documents

**For HTML documents:**

```bash
python src/ingest/ingest_to_db.py --html path/to/document.html
```

**For PDF documents:**

First, extract and structure the PDF into JSONL chunks:

```bash
python src/ingest/ingest_pdf.py path/to/document.pdf --out path/to/chunks.jsonl
```

Then generate embeddings and store the chunks in PostgreSQL:

```bash
python src/ingest/ingest_to_db.py --jsonl path/to/chunks.jsonl
```

The ingestion pipeline generates embeddings using `BAAI/bge-small-en-v1.5` and stores the document content, vectors, and associated metadata.

### 6. Run the assistant

You can interact with the assistant directly through the command line:

```bash
python ask_assistant.py
```

### 7. Start the FastAPI backend

```bash
python -m uvicorn api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

**Available endpoints:**

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/` | API information |
| POST | `/ask` | Submit a question and receive an answer with sources |

Example request:

```json
{
  "question": "What are Solar Renewable Energy Certificates?"
}
```

### 8. Run the frontend

Navigate to the frontend directory:

```bash
cd frontend
npm install
```

Create a `.env.local` file inside `frontend/`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

## Evaluation and Testing

The project includes separate scripts for checking database connectivity, document ingestion, and semantic retrieval.

```bash
python test_db.py
python test_ingestion.py
python test_retrieval.py
```

The `eval/golden.jsonl` file contains reference questions for evaluating retrieval against the renewable energy and SREC knowledge base.

Database and retrieval checks require a configured database and indexed documents.

## Current Scope

The application currently demonstrates document-grounded question answering using a pre-indexed renewable energy knowledge base.

Additional documents can be incorporated through the ingestion scripts. Document ingestion is currently handled through the backend rather than a file-upload interface.

The system is designed to make technical and policy information easier to search, understand, and verify through source-backed AI responses.

---

**Author:** [Sherry Mohareb](https://github.com/Sherry2005)
