"""HR Buddy — FastAPI app entry point."""
import logging
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import ChatRequest, ChatResponse, Citation, HealthResponse, IngestResponse
from .services.pdf_ingest import (
    ingest, load_store, clear_store, store_count, _get_embedding_fn,
)
from .services.retriever import retrieve
from .services.prompt_builder import build_prompt, build_fallback_answer
from .services.llm import chat_complete

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hr_buddy")

# ── shared app state ────────────────────────────────────────────────────────

_state: dict = {
    "embeddings": None,   # np.ndarray | None
    "chunks": [],         # list[dict]
    "embed_fn": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    logger.info("HR Buddy starting — loading vector store…")
    try:
        _state["embed_fn"] = _get_embedding_fn(
            cfg.embedding_provider, cfg.embedding_model, cfg.hf_token
        )
        emb, chunks = load_store(cfg.chroma_dir)
        _state["embeddings"] = emb
        _state["chunks"] = chunks
        logger.info("Vector store ready — %d chunks", len(chunks))
    except Exception as exc:
        logger.error("Startup error: %s", exc)
    yield
    logger.info("HR Buddy shutting down")


app = FastAPI(title="HR Buddy", version="1.0.0", lifespan=lifespan)

# ── CORS ───────────────────────────────────────────────────────────────────

cfg = get_settings()
origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── routes ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    count = len(_state["chunks"])
    return HealthResponse(status="ok", index_ready=count > 0, chunks_count=count)


@app.post("/ingest-pdf", response_model=IngestResponse)
def ingest_pdf():
    """Ingest (or re-ingest) the PDF. Safe to call multiple times."""
    cfg = get_settings()
    try:
        result = ingest(
            pdf_path=cfg.pdf_path,
            store_dir=cfg.chroma_dir,
            embedding_provider=cfg.embedding_provider,
            embedding_model=cfg.embedding_model,
            hf_token=cfg.hf_token,
        )
        # Reload into memory
        emb, chunks = load_store(cfg.chroma_dir)
        _state["embeddings"] = emb
        _state["chunks"] = chunks
        return IngestResponse(status="ok", **result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Ingest failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Answer a policy question grounded in the indexed PDF."""
    cfg = get_settings()
    embeddings = _state["embeddings"]
    chunks = _state["chunks"]
    embed_fn = _state["embed_fn"]

    if embed_fn is None:
        raise HTTPException(status_code=503, detail="Embedding model not ready")
    if embeddings is None or len(chunks) == 0:
        raise HTTPException(status_code=503, detail="Index not ready — call /ingest-pdf first")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    # 1. Retrieve
    results = retrieve(req.message, embeddings, chunks, embed_fn, top_k=cfg.top_k)

    # 2. Citations (deduplicated by page)
    seen_pages: set[int] = set()
    citations: list[Citation] = []
    for c in results:
        if c.page not in seen_pages:
            snippet = c.text[:200].rstrip()
            if len(c.text) > 200:
                snippet += "…"
            citations.append(Citation(page=c.page, snippet=snippet))
            seen_pages.add(c.page)

    # 3. Generate
    system_msg, user_msg = build_prompt(req.message, results)
    answer = chat_complete(
        system=system_msg,
        user=user_msg,
        base_url=cfg.llm_base_url,
        api_key=cfg.llm_api_key,
        model=cfg.llm_model,
        temperature=cfg.llm_temperature,
        max_tokens=cfg.llm_max_tokens,
    )
    if answer is None:
        answer = build_fallback_answer(req.message, results)

    return ChatResponse(
        answer=answer,
        citations=citations,
        matched_chunks=[c.text for c in results],
    )


@app.delete("/reset-index")
def reset_index():
    """Delete stored vectors (call /ingest-pdf to rebuild)."""
    cfg = get_settings()
    deleted = clear_store(cfg.chroma_dir)
    _state["embeddings"] = None
    _state["chunks"] = []
    return {"status": "ok", "deleted": deleted}
