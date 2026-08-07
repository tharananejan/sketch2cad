"""FastAPI dependencies for constructing the planner service."""

from __future__ import annotations

from functools import lru_cache

from .config import PlannerSettings
from .providers import DeepSeekProvider, GroqProvider, LLMProvider
from .service import PlannerService


@lru_cache(maxsize=1)
def get_planner_service() -> PlannerService:
    """Create the configured planner service once per process."""

    settings = PlannerSettings.from_environment()
    provider = _create_provider(settings.provider.name, settings)
    return PlannerService(provider)


def _create_provider(provider_name: str, settings: PlannerSettings) -> LLMProvider:
    if provider_name == "gemini":
        from .providers.openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider(settings.provider)
    if provider_name == "groq":
        return GroqProvider(settings.provider)
    return DeepSeekProvider(settings.provider)
