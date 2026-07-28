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
    def __init__(self, response: str | list[str]) -> None:
        self.responses = [response] if isinstance(response, str) else response
        self.calls: list[tuple[str, str]] = []

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        response_index = min(len(self.calls) - 1, len(self.responses) - 1)
        return self.responses[response_index]


def planned_response(steps: list[dict[str, object]]) -> str:
    return json.dumps({"status": "planned", "steps": steps})


def ready_response() -> str:
    return json.dumps({"status": "ready", "questions": []})


def needs_parameters_response(questions: list[dict[str, object]]) -> str:
    return json.dumps({"status": "needs_parameters", "questions": questions})


def parameter_question(
    parameter_id: str,
    question: str,
    reason: str,
    *,
    value_type: str = "dimension",
    issue: str | None = None,
    current_value: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "parameter_id": parameter_id,
        "question": question,
        "value_type": value_type,
        "unit": None,
        "options": [],
        "reason": reason,
    }
    if value_type == "dimension":
        payload["unit_options"] = ["mm", "cm", "inch"]
    if issue is not None:
        payload["issue"] = issue
    if current_value is not None:
        payload["current_value"] = current_value
    return payload


def test_valid_planning_returns_strict_complex_plan() -> None:
    provider = FakeProvider(
        [
            ready_response(),
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
            ),
            ready_response(),
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
            ),
        ]
    )
    service = PlannerService(provider)
    request = PlannerRequest(
        request="Design a 120 mm by 80 mm mounting plate with 6 mm thickness and four raised mounting bosses.",
        context={"expected_design": "Mounting plate", "completed_steps": [], "remaining_steps": [], "errors": []},
    )

    response = service.plan(request)

    assert response.complexity == "complex"
    assert response.status == "planned"
    assert [step.step_id for step in response.steps] == [1, 2]
    assert response.steps[1].depends_on == [1]
    assert response.plan_id == service.plan(request).plan_id
    assert len(provider.calls) == 4


def test_malformed_json_after_parse_retry_raises_structured_error() -> None:
    service = PlannerService(FakeProvider('{"status":"planned","steps":[}'))

    with pytest.raises(MalformedModelResponseError) as captured_error:
        service.plan(PlannerRequest(request="Create a modular storage enclosure."))

    assert captured_error.value.code == "malformed_model_response"
    assert captured_error.value.details == {"parse_attempts": 2}


def test_empty_request_is_rejected_before_provider_call() -> None:
    provider = FakeProvider(ready_response())
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
                    "questions": [],
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
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create cube volume",
                        "description": "Create an equal-sided cube using the answered side length and selected unit.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube",
            context={"parameter_answers": {"side_length": {"value": 40, "unit": "mm"}}},
        )
    )
    user_prompt = json.loads(provider.calls[0][1])

    assert response.status == "planned"
    assert len(provider.calls) == 2
    assert user_prompt["context"]["parameter_answers"] == {"side_length": {"value": 40.0, "unit": "mm"}}


def test_pending_unanswered_question_prevents_planning_without_provider_call() -> None:
    provider = FakeProvider(
        planned_response(
            [
                {
                    "step_id": 1,
                    "title": "Create cube",
                    "description": "Create the cube even though the side length is missing.",
                    "depends_on": [],
                }
            ]
        )
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube",
            context={
                "pending_questions": [
                    parameter_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length.",
                    )
                ]
            },
        )
    )

    assert response.status == "needs_parameters"
    assert [question.parameter_id for question in response.questions] == ["side_length"]
    assert provider.calls == []


def test_audit_stage_rejects_provider_plan_steps() -> None:
    service = PlannerService(
        FakeProvider(
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create mug body",
                        "description": "Create a mug body before asking for missing dimensions.",
                        "depends_on": [],
                    }
                ]
            )
        )
    )

    with pytest.raises(InvalidModelResponseError):
        service.plan(PlannerRequest(request="Design a coffee mug"))


def test_ready_audit_for_vague_mug_still_returns_questions_without_planning() -> None:
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create mug body",
                        "description": "Create a mug before collecting missing dimensions.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(PlannerRequest(request="Design a coffee mug"))

    assert response.status == "needs_parameters"
    assert {question.parameter_id for question in response.questions} == {
        "mug_height",
        "outer_diameter",
        "wall_thickness",
        "handle_clearance",
    }
    assert len(provider.calls) == 1


def test_ready_audit_for_partial_mug_dimensions_asks_only_missing_questions() -> None:
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create partial mug",
                        "description": "Create a mug despite missing wall and handle details.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(request="Design a coffee mug with 95 mm height and 80 mm outside diameter")
    )

    assert response.status == "needs_parameters"
    assert [question.parameter_id for question in response.questions] == ["wall_thickness", "handle_clearance"]
    assert len(provider.calls) == 1


def test_ready_audit_for_unitless_dimension_returns_correction_without_planning() -> None:
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create cube",
                        "description": "Create a cube with a unitless side length.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(PlannerRequest(request="Generate a cube with side length 40"))

    assert response.status == "needs_parameters"
    assert response.questions[0].parameter_id == "side_length"
    assert response.questions[0].issue == "Dimension is missing a unit."
    assert response.questions[0].current_value == 40
    assert len(provider.calls) == 1


def test_ready_audit_for_complete_cube_dimension_allows_planning() -> None:
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create cube",
                        "description": "Create the cube using the supplied 40 mm side length.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(PlannerRequest(request="Generate a cube with side length 40 mm"))

    assert response.status == "planned"
    assert len(provider.calls) == 2


def test_ready_audit_for_generic_single_dimension_asks_missing_envelope_questions() -> None:
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create bracket",
                        "description": "Create a bracket from one supplied dimension.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(PlannerRequest(request="Design a bracket with 50 mm length"))

    assert response.status == "needs_parameters"
    assert [question.parameter_id for question in response.questions] == ["overall_width", "overall_height"]
    assert len(provider.calls) == 1


def test_partial_pending_answers_reask_only_unanswered_questions() -> None:
    provider = FakeProvider(ready_response())
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Design a coffee mug",
            context={
                "pending_questions": [
                    parameter_question("mug_height", "What height should the mug be?", "The mug body needs a height."),
                    parameter_question(
                        "wall_thickness",
                        "What wall thickness should the mug have?",
                        "Wall thickness is needed for a hollow vessel.",
                    ),
                ],
                "parameter_answers": {"mug_height": {"value": 95, "unit": "mm"}},
            },
        )
    )

    assert response.status == "needs_parameters"
    assert [question.parameter_id for question in response.questions] == ["wall_thickness"]
    assert provider.calls == []


def test_valid_pending_dimension_answer_allows_audit_and_planning() -> None:
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create cube volume",
                        "description": "Create the cube using the selected centimeter side length.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube",
            context={
                "pending_questions": [
                    parameter_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length.",
                    )
                ],
                "parameter_answers": {"side_length": {"value": 4, "unit": "cm"}},
            },
        )
    )
    audit_prompt = json.loads(provider.calls[0][1])

    assert response.status == "planned"
    assert len(provider.calls) == 2
    assert audit_prompt["context"]["parameter_answers"] == {"side_length": {"value": 4.0, "unit": "cm"}}


def test_audit_does_not_repeat_already_valid_parameter_questions() -> None:
    provider = FakeProvider(
        [
            needs_parameters_response(
                [
                    parameter_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length.",
                    )
                ]
            ),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create cube volume",
                        "description": "Create the cube using the confirmed 40 mm side length.",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube",
            context={
                "pending_questions": [
                    parameter_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length.",
                    )
                ],
                "parameter_answers": {"side_length": {"value": 40, "unit": "mm"}},
            },
        )
    )

    assert response.status == "planned"
    assert len(provider.calls) == 2


def test_new_audit_question_is_returned_without_repeating_valid_answers() -> None:
    provider = FakeProvider(
        needs_parameters_response(
            [
                parameter_question(
                    "side_length",
                    "What side length should the cube have?",
                    "A cube requires one equal side length.",
                ),
                parameter_question(
                    "edge_chamfer",
                    "What edge chamfer should the cube have?",
                    "The requested edge treatment needs a chamfer value.",
                ),
            ]
        )
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube with chamfered edges",
            context={
                "pending_questions": [
                    parameter_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length.",
                    )
                ],
                "parameter_answers": {"side_length": {"value": 40, "unit": "mm"}},
            },
        )
    )

    assert response.status == "needs_parameters"
    assert [question.parameter_id for question in response.questions] == ["edge_chamfer"]
    assert len(provider.calls) == 1


@pytest.mark.parametrize(
    ("answer", "expected_issue", "expected_current_value"),
    [
        ({"value": -4, "unit": "mm"}, "Dimension value must be greater than zero.", {"value": -4.0, "unit": "mm"}),
        ({"value": 0, "unit": "cm"}, "Dimension value must be greater than zero.", {"value": 0.0, "unit": "cm"}),
        ({"value": 40}, "Dimension answers must include both a numeric value and a unit.", {"value": 40}),
        (40, "Dimension answers must include both a numeric value and a unit.", 40),
    ],
)
def test_invalid_pending_dimension_answers_return_correction_question(
    answer: object,
    expected_issue: str,
    expected_current_value: object,
) -> None:
    provider = FakeProvider(ready_response())
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Generate a cube",
            context={
                "pending_questions": [
                    parameter_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length.",
                    )
                ],
                "parameter_answers": {"side_length": answer},
            },
        )
    )

    assert response.status == "needs_parameters"
    assert response.questions[0].parameter_id == "side_length"
    assert response.questions[0].issue == expected_issue
    current_value = response.questions[0].current_value
    if hasattr(current_value, "model_dump"):
        current_value = current_value.model_dump(mode="json")
    assert current_value == expected_current_value
    assert provider.calls == []


def test_audit_returns_contradictory_dimension_issue_without_planning() -> None:
    provider = FakeProvider(
        needs_parameters_response(
            [
                parameter_question(
                    "wall_thickness",
                    "What wall thickness should the mug have?",
                    "Wall thickness must fit inside the mug diameter.",
                    issue="Wall thickness cannot be greater than or equal to the outer radius.",
                    current_value={"value": 50, "unit": "mm"},
                )
            ]
        )
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request="Design a mug with 80 mm outer diameter and 50 mm wall thickness",
            context={
                "parameter_answers": {
                    "outer_diameter": {"value": 80, "unit": "mm"},
                    "wall_thickness": {"value": 50, "unit": "mm"},
                }
            },
        )
    )

    assert response.status == "needs_parameters"
    assert response.questions[0].issue == "Wall thickness cannot be greater than or equal to the outer radius."
    assert len(provider.calls) == 1


def test_needs_parameters_requires_non_empty_questions() -> None:
    service = PlannerService(FakeProvider(needs_parameters_response([])))

    with pytest.raises(InvalidModelResponseError):
        service.plan(PlannerRequest(request="Design a coffee mug"))


def test_dimension_questions_default_unit_options_for_ui_dropdown() -> None:
    question = parameter_question("side_length", "What side length should the cube have?", "A cube requires one equal side length.")
    question.pop("unit_options")
    service = PlannerService(FakeProvider(needs_parameters_response([question])))

    response = service.plan(PlannerRequest(request="Generate a cube"))

    assert response.status == "needs_parameters"
    assert response.questions[0].unit_options == ["mm", "cm", "inch"]


def test_needs_parameters_rejects_invalid_question_type() -> None:
    invalid_question = parameter_question("side_length", "What side length should the cube have?", "A side length is required.")
    invalid_question["value_type"] = "linear_dimension"
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
    service = PlannerService(FakeProvider([ready_response(), planned_response(steps)]))
    request = PlannerRequest(
        request=(
            "Design a thirty-feature 300 mm by 200 mm by 120 mm industrial enclosure "
            "with sequential structural and interface details."
        ),
        context={"expected_design": "Industrial enclosure", "completed_steps": [], "remaining_steps": [], "errors": []},
    )

    response = service.plan(request)

    assert len(response.steps) == 30
    assert response.steps[-1].step_id == 30
    assert response.steps[-1].depends_on == [29]
