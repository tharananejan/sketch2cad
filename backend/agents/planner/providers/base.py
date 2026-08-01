"""Provider contract used by planner logic."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Generates a raw JSON response from a configured language model."""

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return the model content for one planner request."""
