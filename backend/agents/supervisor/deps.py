"""
Dependencies and configuration settings for the Supervisor Agent.
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


@lru_cache
def get_settings() -> Settings:
    """FastAPI dependency to retrieve singleton settings instance."""
    return Settings()
