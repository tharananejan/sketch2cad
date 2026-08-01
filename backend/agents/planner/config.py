"""Environment-backed configuration for planner LLM providers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .errors import PlannerConfigurationError


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Connection settings for one OpenAI-compatible LLM provider."""

    name: str
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float
    max_output_tokens: int


@dataclass(frozen=True, slots=True)
class PlannerSettings:
    """Resolved runtime settings for the planner service."""

    provider: ProviderConfig

    @classmethod
    def from_environment(cls) -> "PlannerSettings":
        """Build planner settings from environment variables."""

        load_dotenv(Path(__file__).with_name(".env"))

        provider_name = os.getenv("PLANNER_PROVIDER", "groq").strip().lower()
        if provider_name not in {"groq", "deepseek"}:
            raise PlannerConfigurationError(
                "PLANNER_PROVIDER must be either 'groq' or 'deepseek'.",
                details={"provider": provider_name},
            )

        prefix = provider_name.upper()
        api_key = _required_environment_value(f"{prefix}_API_KEY")
        model = _required_environment_value(f"{prefix}_MODEL")
        base_url = os.getenv(f"{prefix}_BASE_URL", _default_base_url(provider_name)).strip()
        timeout_seconds = _positive_float("PLANNER_TIMEOUT_SECONDS", "30")
        max_output_tokens = _positive_int("PLANNER_MAX_OUTPUT_TOKENS", "2048")

        return cls(
            provider=ProviderConfig(
                name=provider_name,
                api_key=api_key,
                model=model,
                base_url=base_url.rstrip("/"),
                timeout_seconds=timeout_seconds,
                max_output_tokens=max_output_tokens,
            )
        )


def _required_environment_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise PlannerConfigurationError(
            f"{name} must be configured.",
            details={"setting": name},
        )
    return value


def _positive_float(name: str, default: str) -> float:
    raw_value = os.getenv(name, default)
    try:
        value = float(raw_value)
    except ValueError as error:
        raise PlannerConfigurationError(
            f"{name} must be a positive number.",
            details={"setting": name},
        ) from error
    if value <= 0:
        raise PlannerConfigurationError(
            f"{name} must be a positive number.",
            details={"setting": name},
        )
    return value


def _positive_int(name: str, default: str) -> int:
    raw_value = os.getenv(name, default)
    try:
        value = int(raw_value)
    except ValueError as error:
        raise PlannerConfigurationError(
            f"{name} must be a positive integer.",
            details={"setting": name},
        ) from error
    if value <= 0:
        raise PlannerConfigurationError(
            f"{name} must be a positive integer.",
            details={"setting": name},
        )
    return value


def _default_base_url(provider_name: str) -> str:
    if provider_name == "groq":
        return "https://api.groq.com/openai/v1"
    return "https://api.deepseek.com"
