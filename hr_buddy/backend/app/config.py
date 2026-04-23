"""Central config — reads from .env via pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Embedding
    embedding_provider: str = "local"          # "local" | "hf_inference"
    hf_token: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # LLM (OpenAI-compatible)
    llm_base_url: str = ""                     # e.g. https://api.openai.com/v1
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024

    # Vector store (numpy .npy + .json, stored in this directory)
    chroma_dir: str = "./app/data/store"  # kept as chroma_dir for .env compatibility

    # PDF
    pdf_path: str = "../../SkillSync_Company_Policy_2026.pdf"

    # Retrieval
    top_k: int = 5

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"


@lru_cache
def get_settings() -> Settings:
    return Settings()
