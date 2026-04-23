"""Request / response models."""
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class Citation(BaseModel):
    page: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    matched_chunks: Optional[list[str]] = None


class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    pages_processed: int


class HealthResponse(BaseModel):
    status: str
    index_ready: bool
    chunks_count: int
