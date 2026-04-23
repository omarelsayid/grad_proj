"""Cosine-similarity retrieval over the numpy vector store."""
import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger("hr_buddy.retriever")


@dataclass
class RetrievedChunk:
    text: str
    page: int
    score: float


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Batch cosine similarity: query (D,) vs matrix (N, D) → scores (N,)."""
    q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    normed = matrix / norms
    return normed @ q


def retrieve(
    query: str,
    embeddings: np.ndarray,
    chunks: list[dict],
    embed_fn,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    if embeddings is None or len(chunks) == 0:
        logger.warning("Vector store is empty — run /ingest-pdf first")
        return []

    query_vec = np.array(embed_fn([query])[0], dtype=np.float32)
    scores = _cosine_similarity(query_vec, embeddings)
    top_indices = np.argsort(scores)[::-1][: min(top_k, len(chunks))]

    results = []
    for idx in top_indices:
        c = chunks[idx]
        results.append(RetrievedChunk(
            text=c["text"],
            page=c["page"],
            score=float(scores[idx]),
        ))
    logger.debug("Top score=%.3f for query: %s…", results[0].score if results else 0, query[:60])
    return results
