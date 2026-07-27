from __future__ import annotations

import json

import pytest

from backend.agents.planner.errors import (
    InvalidRequestError,
    MalformedModelResponseError,
    UnsupportedRequestError,
)
from backend.agents.planner.models import PlannerRequest
from backend.agents.planner.service import PlannerService


class FakeProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


def planned_response(steps: list[dict[str, object]]) -> str:
    return json.dumps({"status": "planned", "steps": steps})


def test_valid_planning_returns_strict_complex_plan() -> None:
    provider = FakeProvider(
        planned_response(
            [
                {
                    "step_id": 1,
                    "title": "Establish base profile",
                    "description": "Create the rectangular base profile using the requested footprint dimensions.",
                    "depends_on": [],
                },
                {
                    "step_id": 2,
                    "title": "Form mounting features",
                    "description": "Add the mounting bosses at the specified locations on the completed base.",
                    "depends_on": [1],
                },
            ]
        )
    )
    service = PlannerService(provider)
    request = PlannerRequest(
        request="Design a mounting plate with four raised mounting bosses.",
        context={"expected_design": "Mounting plate", "completed_steps": [], "remaining_steps": [], "errors": []},
    )

    response = service.plan(request)

    assert response.complexity == "complex"
    assert [step.step_id for step in response.steps] == [1, 2]
    assert response.steps[1].depends_on == [1]
    assert response.plan_id == service.plan(request).plan_id
    assert len(provider.calls) == 2


def test_malformed_json_after_parse_retry_raises_structured_error() -> None:
    service = PlannerService(FakeProvider('{"status":"planned","steps":[}'))

    with pytest.raises(MalformedModelResponseError) as captured_error:
        service.plan(PlannerRequest(request="Create a modular storage enclosure."))

    assert captured_error.value.code == "malformed_model_response"
    assert captured_error.value.details == {"parse_attempts": 2}


def test_empty_request_is_rejected_before_provider_call() -> None:
    provider = FakeProvider(planned_response([]))
    service = PlannerService(provider)

    with pytest.raises(InvalidRequestError):
        service.plan(PlannerRequest(request="   "))

    assert provider.calls == []


def test_unsupported_request_returns_structured_error() -> None:
    service = PlannerService(
        FakeProvider(
            json.dumps(
                {
                    "status": "unsupported",
                    "reason": "This is not a CAD modeling request.",
                    "steps": [],
                }
            )
        )
    )

    with pytest.raises(UnsupportedRequestError) as captured_error:
        service.plan(PlannerRequest(request="Explain the history of jazz music."))

    assert captured_error.value.code == "unsupported_request"


def test_large_request_preserves_ordered_dependencies() -> None:
    steps = [
        {
            "step_id": step_id,
            "title": f"Model assembly feature {step_id}",
            "description": f"Create the required engineering feature number {step_id} for the assembly.",
            "depends_on": [] if step_id == 1 else [step_id - 1],
        }
        for step_id in range(1, 31)
    ]
    service = PlannerService(FakeProvider(planned_response(steps)))
    request = PlannerRequest(
        request="Design a thirty-feature industrial enclosure with sequential structural and interface details.",
        context={"expected_design": "Industrial enclosure", "completed_steps": [], "remaining_steps": [], "errors": []},
    )

    response = service.plan(request)

    assert len(response.steps) == 30
    assert response.steps[-1].step_id == 30
    assert response.steps[-1].depends_on == [29]
