"""
Dependencies and configuration settings for the Code Generator Agent.
"""

import os
from functools import lru_cache


class Settings:
    """Configuration settings loaded from environment variables with sensible defaults."""

    def __init__(self) -> None:
        self.OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5-coder:0.5b")
        self.EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text")

        # RAG Chunking and Retrieval parameters
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.TOP_K: int = int(os.getenv("TOP_K", "3"))
        self.RAG_MAX_DISTANCE: float = float(os.getenv("RAG_MAX_DISTANCE", "0.65"))

        # Paths
        self.PROJECT_ROOT: str = os.path.dirname(os.path.abspath(__file__))
        self.KNOWLEDGE_DIR: str = os.path.join(self.PROJECT_ROOT, "knowledge_base")
        self.CHROMA_PERSIST_DIR: str = os.path.join(self.PROJECT_ROOT, "chroma_db")
        self.PROMPTS_DIR: str = os.path.join(self.PROJECT_ROOT, "prompts")

        # Ensure required directories exist
        os.makedirs(self.KNOWLEDGE_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """FastAPI dependency to retrieve singleton settings instance."""
    return Settings()
