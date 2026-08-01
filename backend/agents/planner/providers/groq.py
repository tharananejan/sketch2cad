"""Groq provider adapter for development and testing deployments."""

from __future__ import annotations

from ..config import ProviderConfig
from .openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    """OpenAI-compatible planner adapter backed by Groq."""

    def __init__(self, config: ProviderConfig) -> None:
        if config.name != "groq":
            raise ValueError("GroqProvider requires a Groq provider configuration.")
        super().__init__(config)
