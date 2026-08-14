# Enterprise Agentic RAG

A production-ready full-stack Agentic RAG application with hybrid search, multi-stage validation, and an interactive inspector UI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │  /ingest      │  │  /query                          │ │
│  │  - Dropzone   │  │  - Chat Feed (streaming)         │ │
│  │  - Pipeline   │  │  - Inspector Drawer              │ │
│  │  - Chunks     │  │    - Retrieval Breakdown         │ │
│  └──────┬───────┘  │    - Reasoning Plan              │ │
│         │          │    - Validation Badges            │ │
│         │          └──────────┬─────────────────────────┘│
└─────────┼───────────────────┼───────────────────────────┘
          │  SSE              │  SSE
┌─────────▼───────────────────▼───────────────────────────┐
│                   FastAPI Backend                         │
│  ┌─────────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │  Ingestion   │  │  Agent   │  │  Validation Nodes  │  │
│  │  Pipeline    │  │  (Lang-  │  │  - Gatekeeper      │  │
│  │  - Parse     │  │   Graph) │  │  - Auditor         │  │
│  │  - Chunk     │  │  - Plan  │  │  - Strategist      │  │
│  │  - Enrich    │  │  - Tools │  └────────────────────┘  │
│  └──────┬──────┘  └────┬─────┘                           │
│         │              │                                  │
│  ┌──────▼──────────────▼─────────────────────────────┐   │
│  │              Qdrant Hybrid Store                    │   │
│  │  Dense (text-embedding-3-small) + Sparse (BM25)    │   │
│  │  → RRF Fusion → Cross-Encoder Reranker             │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### 1. Start Qdrant
```bash
docker compose up -d
```

### 2. Backend
```bash
cd backend
cp .env.example .env  # Fill in your OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### 4. Open
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, LangGraph, LangChain |
| Vector DB | Qdrant (Hybrid: Dense + Sparse) |
| Embeddings | OpenAI text-embedding-3-small + BM25 |
| Reranker | Cross-Encoder (ms-marco-MiniLM-L-6-v2) |
| Evaluation | RAGAS, Red-team harness |

## Project Structure

```
Enterprise-RAG/
├── docker-compose.yml          # Qdrant infrastructure
├── frontend/                   # Next.js application
│   └── src/
│       ├── app/               # App Router pages
│       ├── components/        # UI components
│       └── hooks/             # Custom React hooks
├── backend/                   # FastAPI application
│   └── app/
│       ├── ingestion/         # Document processing pipeline
│       ├── retrieval/         # Qdrant + embeddings + reranker
│       ├── agent/             # LangGraph agentic orchestration
│       ├── validation/        # Gatekeeper/Auditor/Strategist
│       └── routers/           # API endpoints
└── tests/                     # Evaluation & red-team tests
```
