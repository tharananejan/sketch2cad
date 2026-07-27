"""Core Frontier Planning Agent orchestration logic."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from pydantic import ValidationError

from .errors import (
    InvalidModelResponseError,
    InvalidRequestError,
    MalformedModelResponseError,
    UnsupportedRequestError,
)
from .models import PlanDraft, PlanResponse, PlanStep, PlannerRequest
from .prompts.system_prompt import PLANNER_SYSTEM_PROMPT
from .providers.base import LLMProvider

_FORBIDDEN_OUTPUT_PATTERNS = (
    re.compile(r"```", re.IGNORECASE),
    re.compile(r"\bpython\b", re.IGNORECASE),
    re.compile(r"\bfreecad\b", re.IGNORECASE),
    re.compile(r"\bapi\b", re.IGNORECASE),
    re.compile(r"\bimport\s+\w+", re.IGNORECASE),
    re.compile(r"\bdef\s+\w+", re.IGNORECASE),
    re.compile(r"\bhttps?://", re.IGNORECASE),
)


class PlannerService:
    """Produces validated complex CAD modeling plans using an injected provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def plan(self, planner_request: PlannerRequest) -> PlanResponse:
        """Create one strict modeling plan from a complex request and its context."""

        if not planner_request.request.strip():
            raise InvalidRequestError("The request must not be empty.")

        user_prompt = self._build_user_prompt(planner_request)
        raw_response = self._provider.generate(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        draft = self._parse_draft(raw_response)

        if draft.status == "unsupported":
            raise UnsupportedRequestError(
                draft.reason or "The request is not supported for CAD modeling.",
            )

        self._ensure_modeling_only(draft.steps)
        return PlanResponse(
            plan_id=self._derive_plan_id(planner_request),
            complexity="complex",
            steps=draft.steps,
        )

    @staticmethod
    def _build_user_prompt(planner_request: PlannerRequest) -> str:
        payload = planner_request.model_dump(mode="json")
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _derive_plan_id(planner_request: PlannerRequest) -> str:
        canonical_input = json.dumps(
            planner_request.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_input))

    def _parse_draft(self, raw_response: str) -> PlanDraft:
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            try:
                payload = self._extract_json_object(raw_response)
            except json.JSONDecodeError as error:
                raise MalformedModelResponseError(
                    "The planner provider returned malformed JSON after one parse retry.",
                    details={"parse_attempts": 2},
                ) from error

        try:
            return PlanDraft.model_validate(payload)
        except ValidationError as error:
            raise InvalidModelResponseError(
                "The planner provider returned JSON outside the planner contract.",
                details={"validation_errors": error.errors(include_url=False)},
            ) from error

    @staticmethod
    def _extract_json_object(raw_response: str) -> Any:
        stripped_response = raw_response.strip()
        if stripped_response.startswith("```") and stripped_response.endswith("```"):
            stripped_response = stripped_response.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        start_index = stripped_response.find("{")
        if start_index < 0:
            raise json.JSONDecodeError("No JSON object found", stripped_response, 0)
        payload, end_index = json.JSONDecoder().raw_decode(stripped_response[start_index:])
        if stripped_response[start_index + end_index :].strip():
            raise json.JSONDecodeError("Unexpected content after JSON object", stripped_response, start_index + end_index)
        return payload

    @staticmethod
    def _ensure_modeling_only(steps: list[PlanStep]) -> None:
        for step in steps:
            step_text = f"{step.title}\n{step.description}"
            for pattern in _FORBIDDEN_OUTPUT_PATTERNS:
                if pattern.search(step_text):
                    raise InvalidModelResponseError(
                        "The planner provider returned prohibited implementation content.",
                        details={"step_id": step.step_id},
                    )
