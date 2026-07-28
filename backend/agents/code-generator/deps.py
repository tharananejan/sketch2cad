"""
Dependencies and configuration settings for the Code Generator Agent.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv, find_dotenv

# Load environment variables from a .env file (looks in current dir and parent dirs)
load_dotenv(find_dotenv())


class Settings:
    """Configuration settings loaded from environment variables with sensible defaults."""

    def __init__(self) -> None:
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

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
