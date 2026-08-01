"""DeepSeek provider adapter for production deployments."""

from __future__ import annotations

from ..config import ProviderConfig
from .openai_compatible import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    """OpenAI-compatible planner adapter backed by DeepSeek."""

    def __init__(self, config: ProviderConfig) -> None:
        if config.name != "deepseek":
            raise ValueError("DeepSeekProvider requires a DeepSeek provider configuration.")
        super().__init__(config)
