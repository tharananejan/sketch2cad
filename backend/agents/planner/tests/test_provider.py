from __future__ import annotations

import json
from typing import Any

from pytest import MonkeyPatch

from backend.agents.planner.config import ProviderConfig
from backend.agents.planner.providers.openai_compatible import OpenAICompatibleProvider


class FakeHTTPResponse:
    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps({"choices": [{"message": {"content": '{"status":"unsupported","reason":"x","steps":[]}'}}]}).encode(
            "utf-8"
        )


def test_provider_sends_product_user_agent(monkeypatch: MonkeyPatch) -> None:
    captured_headers: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured_headers.update(request.header_items())
        assert timeout == 5
        return FakeHTTPResponse()

    monkeypatch.setattr("backend.agents.planner.providers.openai_compatible.urlopen", fake_urlopen)
    provider = OpenAICompatibleProvider(
        ProviderConfig(
            name="groq",
            api_key="test-key",
            model="test-model",
            base_url="https://provider.example/openai/v1",
            timeout_seconds=5,
            max_output_tokens=128,
        )
    )

    provider.generate(system_prompt="Return JSON only.", user_prompt='{"request":"Design a bracket."}')

    assert captured_headers["User-agent"] == "Sketch2CAD-Planner/1.0"
