from __future__ import annotations

import json

import pytest

from backend.agents.planner.errors import (
    InvalidModelResponseError,
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


def needs_parameters_response(questions: list[dict[str, object]]) -> str:
    return json.dumps({"status": "needs_parameters", "questions": questions})


def parameter_question(parameter_id: str, question: str, reason: str) -> dict[str, object]:
    return {
        "parameter_id": parameter_id,
        "question": question,
        "value_type": "number",
        "unit": "mm",
        "options": [],
        "reason": reason,
    }


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
    assert response.status == "planned"
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


def test_coffee_mug_request_returns_mug_specific_parameter_questions() -> None:
    service = PlannerService(
        FakeProvider(
            needs_parameters_response(
                [
                    parameter_question("mug_height", "What height should the mug be?", "The mug body height defines the main vessel volume."),
                    parameter_question(
                        "outer_diameter",
                        "What outside diameter should the mug have?",
                        "The outside diameter defines the cylindrical body footprint.",
                    ),
                    parameter_question(
                        "wall_thickness",
                        "What wall thickness should the mug have?",
                        "Wall thickness is needed to create a hollow printable vessel.",
                    ),
                    parameter_question(
                        "handle_clearance",
                        "What finger clearance should the handle provide?",
                        "Handle clearance controls the functional opening size.",
                    ),
                ]
            )
        )
    )

    response = service.plan(PlannerRequest(request="Design a coffee mug"))

    assert response.status == "needs_parameters"
    assert {question.parameter_id for question in response.questions} == {
        "mug_height",
        "outer_diameter",
        "wall_thickness",
        "handle_clearance",
    }


def test_cube_request_returns_cube_specific_dimension_questions() -> None:
    service = PlannerService(
        FakeProvider(
            needs_parameters_response(
                [
                    parameter_question("side_length", "What side length should the cube have?", "A cube requires one equal side length."),
                ]
            )
        )
    )

    response = service.plan(PlannerRequest(request="Generate a cube"))

    assert response.status == "needs_parameters"
    assert [question.parameter_id for question in response.questions] == ["side_length"]


def test_phone_holder_request_returns_fit_and_angle_questions() -> None:
    service = PlannerService(
        FakeProvider(
            needs_parameters_response(
                [
                    parameter_question("phone_width", "What phone width should the holder fit?", "The slot width must match the phone."),
                    parameter_question(
                        "phone_thickness",
                        "What phone thickness should the slot accept?",
                        "The slot gap must fit the phone thickness.",
                    ),
                    parameter_question("holder_angle", "What viewing angle should the holder use?", "The back support angle sets the phone tilt."),
                    parameter_question("front_lip_height", "What front lip height should retain the phone?", "The lip prevents the phone from sliding."),
                ]
            )
        )
    )

    response = service.plan(PlannerRequest(request="Generate a phone holder"))

    assert response.status == "needs_parameters"
    assert {question.parameter_id for question in response.questions} == {
        "phone_width",
        "phone_thickness",
        "holder_angle",
        "front_lip_height",
    }


def test_answered_parameter_answers_are_sent_to_provider_for_planning() -> None:
    provider = FakeProvider(
        planned_response(
            [
                {
                    "step_id": 1,
                    "title": "Create cube volume",
                    "description": "Create an equal-sided cube using the answered side length.",
                    "depends_on": [],
                }
            ]
        )
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube",
            context={"parameter_answers": {"side_length": 40}},
        )
    )
    user_prompt = json.loads(provider.calls[0][1])

    assert response.status == "planned"
    assert user_prompt["context"]["parameter_answers"] == {"side_length": 40}


def test_needs_parameters_requires_non_empty_questions() -> None:
    service = PlannerService(FakeProvider(needs_parameters_response([])))

    with pytest.raises(InvalidModelResponseError):
        service.plan(PlannerRequest(request="Design a coffee mug"))


def test_needs_parameters_rejects_invalid_question_type() -> None:
    invalid_question = parameter_question("side_length", "What side length should the cube have?", "A side length is required.")
    invalid_question["value_type"] = "dimension"
    service = PlannerService(FakeProvider(needs_parameters_response([invalid_question])))

    with pytest.raises(InvalidModelResponseError):
        service.plan(PlannerRequest(request="Generate a cube"))


def test_needs_parameters_rejects_duplicate_parameter_ids() -> None:
    service = PlannerService(
        FakeProvider(
            needs_parameters_response(
                [
                    parameter_question("side_length", "What side length should the cube have?", "A side length is required."),
                    parameter_question("side_length", "Confirm the side length.", "A duplicate ID would make answers ambiguous."),
                ]
            )
        )
    )

    with pytest.raises(InvalidModelResponseError):
        service.plan(PlannerRequest(request="Generate a cube"))


def test_needs_parameters_rejects_mixed_steps_and_questions() -> None:
    response = {
        "status": "needs_parameters",
        "questions": [
            parameter_question("side_length", "What side length should the cube have?", "A side length is required."),
        ],
        "steps": [
            {
                "step_id": 1,
                "title": "Create cube",
                "description": "Create the cube body.",
                "depends_on": [],
            }
        ],
    }
    service = PlannerService(FakeProvider(json.dumps(response)))

    with pytest.raises(InvalidModelResponseError):
        service.plan(PlannerRequest(request="Generate a cube"))


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
