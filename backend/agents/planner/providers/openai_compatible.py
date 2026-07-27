"""Minimal OpenAI-compatible HTTP transport shared by provider adapters."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import ProviderConfig
from ..errors import ProviderRequestError


class OpenAICompatibleProvider:
    """Calls a chat-completions endpoint with deterministic JSON settings."""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Submit one planner request and return the assistant message content."""

        payload = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": self._config.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            url=f"{self._config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Sketch2CAD-Planner/1.0",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise ProviderRequestError(
                "The planner provider rejected the request.",
                details={
                    "provider": self._config.name,
                    "status_code": error.code,
                    "response": _read_error_body(error),
                },
            ) from error
        except (URLError, TimeoutError) as error:
            raise ProviderRequestError(
                "The planner provider could not be reached.",
                details={"provider": self._config.name},
            ) from error
        except json.JSONDecodeError as error:
            raise ProviderRequestError(
                "The planner provider returned an invalid HTTP response.",
                details={"provider": self._config.name},
            ) from error

        return _extract_content(response_payload, self._config.name)


def _read_error_body(error: HTTPError) -> str:
    body = error.read().decode("utf-8", errors="replace").strip()
    return body[:1_000]


def _extract_content(payload: dict[str, Any], provider_name: str) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderRequestError(
            "The planner provider response did not contain a completion.",
            details={"provider": provider_name},
        ) from error
    if not isinstance(content, str) or not content.strip():
        raise ProviderRequestError(
            "The planner provider returned an empty completion.",
            details={"provider": provider_name},
        )
    return content
