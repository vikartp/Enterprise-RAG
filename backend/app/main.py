"""Enterprise Agentic RAG Backend — FastAPI Application Entry Point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import ingest, query


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — initialize resources on startup, cleanup on shutdown."""
    settings = get_settings()

    # Initialize Qdrant collection on startup
    from app.retrieval.qdrant_store import ensure_collection

    await ensure_collection()
    print(f"✓ Qdrant collection '{settings.qdrant_collection_name}' ready")
    print(f"✓ Backend running on {settings.backend_host}:{settings.backend_port}")

    yield

    # Cleanup (if needed)
    print("⏹ Shutting down Enterprise RAG Backend")


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Enterprise Agentic RAG",
        description="Production-ready Agentic RAG with Qdrant Hybrid Search, "
        "LangGraph orchestration, and multi-stage validation guardrails.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
    app.include_router(query.router, prefix="/api", tags=["Query"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "enterprise-rag-backend"}

    return app


app = create_app()
