"""PDF loading, page-aware chunking, embedding, and numpy-based vector store."""
import json
import logging
import os
import re
from pathlib import Path

import numpy as np

logger = logging.getLogger("hr_buddy.ingest")

# ── text helpers ────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_page(text: str, page_num: int, chunk_size: int = 700, overlap: int = 150) -> list[dict]:
    chunks = []
    text = text.strip()
    if not text:
        return chunks
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            for sep in ["\n\n", ". ", ".\n", "\n"]:
                idx = text.rfind(sep, start + overlap, end)
                if idx != -1:
                    end = idx + len(sep)
                    break
        chunk_text = _clean(text[start:end])
        if len(chunk_text) > 60:
            chunks.append({"text": chunk_text, "page": page_num, "start_char": start})
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def extract_chunks(pdf_path: str) -> list[dict]:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf not installed — run: pip install pypdf")

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(path))
    all_chunks: list[dict] = []
    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        page_chunks = _split_page(_clean(raw), page_num=i)
        all_chunks.extend(page_chunks)
        logger.debug("Page %d → %d chunks", i, len(page_chunks))
    logger.info("Extracted %d chunks from %d pages", len(all_chunks), len(reader.pages))
    return all_chunks


# ── embeddings ─────────────────────────────────────────────────────────────

def _get_embedding_fn(provider: str, model: str, hf_token: str):
    if provider == "hf_inference":
        if not hf_token:
            raise ValueError("HF_TOKEN required for hf_inference provider")
        import requests
        api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
        headers = {"Authorization": f"Bearer {hf_token}"}

        def embed_hf(texts: list[str]) -> list[list[float]]:
            resp = requests.post(api_url, headers=headers, json={"inputs": texts}, timeout=60)
            resp.raise_for_status()
            return resp.json()

        return embed_hf
    else:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError("sentence-transformers not installed")
        _model = SentenceTransformer(model)

        def embed_local(texts: list[str]) -> list[list[float]]:
            return _model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

        return embed_local


# ── numpy vector store (persisted as .npy + .json) ─────────────────────────

def _store_paths(store_dir: str) -> tuple[str, str]:
    os.makedirs(store_dir, exist_ok=True)
    return (
        os.path.join(store_dir, "embeddings.npy"),
        os.path.join(store_dir, "chunks.json"),
    )


def save_store(store_dir: str, embeddings: np.ndarray, chunks: list[dict]) -> None:
    emb_path, meta_path = _store_paths(store_dir)
    np.save(emb_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    logger.info("Saved %d vectors to %s", len(chunks), store_dir)


def load_store(store_dir: str) -> tuple[np.ndarray | None, list[dict]]:
    emb_path, meta_path = _store_paths(store_dir)
    if not os.path.exists(emb_path) or not os.path.exists(meta_path):
        return None, []
    embeddings = np.load(emb_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    logger.info("Loaded %d vectors from %s", len(chunks), store_dir)
    return embeddings, chunks


def store_count(store_dir: str) -> int:
    _, meta_path = _store_paths(store_dir)
    if not os.path.exists(meta_path):
        return 0
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return len(json.load(f))
    except Exception:
        return 0


def clear_store(store_dir: str) -> int:
    emb_path, meta_path = _store_paths(store_dir)
    count = store_count(store_dir)
    for p in (emb_path, meta_path):
        if os.path.exists(p):
            os.remove(p)
    return count


# ── public ingest API ───────────────────────────────────────────────────────

def ingest(
    pdf_path: str,
    store_dir: str,
    embedding_provider: str,
    embedding_model: str,
    hf_token: str = "",
    batch_size: int = 32,
) -> dict:
    chunks = extract_chunks(pdf_path)
    if not chunks:
        return {"chunks_indexed": 0, "pages_processed": 0}

    embed_fn = _get_embedding_fn(embedding_provider, embedding_model, hf_token)
    texts = [c["text"] for c in chunks]

    all_vecs: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        all_vecs.extend(embed_fn(texts[i : i + batch_size]))
        logger.debug("Embedded batch %d/%d", i // batch_size + 1, -(-len(texts) // batch_size))

    embeddings = np.array(all_vecs, dtype=np.float32)
    save_store(store_dir, embeddings, chunks)

    n_pages = max(c["page"] for c in chunks)
    return {"chunks_indexed": len(chunks), "pages_processed": n_pages}
