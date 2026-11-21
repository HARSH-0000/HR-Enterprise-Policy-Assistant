import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Source
)

from app.rag.crag import build_hr_crag_graph
from app.rag.vectorstore import get_retriever
from app.rag.reranker import rerank_documents

from app.services.chat_service import answer_question


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Preload embedding model (force initialization)
    logger.info("Preloading embedding model...")
    from app.rag.embeddings import get_embedding_model
    app.state.embeddings = get_embedding_model()
    logger.info("Embedding model loaded successfully.")

    # Preload reranker model (force initialization)
    logger.info("Preloading reranker model...")
    from app.rag.reranker import _get_reranker
    app.state.reranker_model = _get_reranker()
    logger.info("Reranker model loaded successfully.")

    # Initialize vector database retriever
    logger.info("Initializing vector store retriever...")
    app.state.retriever = get_retriever()

    # Initialize LangGraph workflow
    logger.info("Building CRAG graph...")
    app.state.crag = build_hr_crag_graph(
        app.state.retriever,
        reranker=rerank_documents
    )

    logger.info("HR Enterprise Assistant is ready.")
    yield


app = FastAPI(
    title="HR Enterprise Assistant API",
    version="0.1.0",
    description=(
        "Phase 1: Policy question answering "
        "over approved HR documents."
    ),
    lifespan=lifespan
)


# Configure frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hr-enterprise-assistant"
    }


@app.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(payload: ChatRequest):
    question = payload.query.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Query cannot be empty."
        )

    try:
        result = answer_question(
            app.state.crag,
            question,
            verify_grounding=payload.verify_grounding
        )
    except Exception as exc:
        logger.exception("CRAG pipeline error")
        raise HTTPException(
            status_code=503,
            detail=(
                "The HR assistant is temporarily "
                "unavailable. Please try again later."
            )
        ) from exc

    # Transform sources to match frontend expectations
    sources = []
    for s in result.get("sources", []):
        source = Source(
            title=s.get("title") or s.get("source", "HR Policy"),
            policy_id=s.get("policy_id", "UNKNOWN"),
            page=s.get("page", 0),
            department=s.get("department", "Human Resources"),
            status=s.get("status", "pending_review"),
            section=s.get("section"),
            version=s.get("version"),
            effective_date=s.get("effective_date")
        )
        sources.append(source)

    return ChatResponse(
        response=result["answer"],
        sources=sources,
        grounded=result.get("grounded"),
        status=result.get("status", "answered")
    )
