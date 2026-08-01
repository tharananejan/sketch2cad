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


def phased_response(phases: list[dict[str, object]]) -> str:
    return json.dumps({"status": "planned", "phases": phases})


def plan_step(step_id: int, *, depends_on: list[int] | None = None, category: str = "primitive") -> dict[str, object]:
    return {
        "step_id": step_id,
        "title": f"Modeling operation {step_id}",
        "description": f"Create the required engineering feature number {step_id}.",
        "category": category,
        "depends_on": depends_on or [],
    }


def plan_phase(
    phase_id: int,
    steps: list[dict[str, object]],
    *,
    title: str = "Construction phase",
    goal: str = "Complete the major independent feature of this phase.",
    depends_on: list[int] | None = None,
) -> dict[str, object]:
    return {
        "phase_id": phase_id,
        "title": title,
        "goal": goal,
        "steps": steps,
        "depends_on": depends_on or [],
    }


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
                        "category": "primitive",
                        "depends_on": [],
                    },
                    {
                        "step_id": 2,
                        "title": "Form mounting features",
                        "description": "Add the mounting bosses at the specified locations on the completed base.",
                        "category": "primitive",
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
                        "category": "primitive",
                        "depends_on": [],
                    },
                    {
                        "step_id": 2,
                        "title": "Form mounting features",
                        "description": "Add the mounting bosses at the specified locations on the completed base.",
                        "category": "primitive",
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
        # Use a request with 3+ measurements and no common-design keyword
        service.plan(PlannerRequest(request="Create a 100 mm by 80 mm by 60 mm modular storage container."))

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
        # Add fake 3+ measurements so fallback is empty, letting the audit run
        service.plan(PlannerRequest(request="Explain the history of jazz music with 100 mm by 80 mm by 60 mm sections."))

    assert captured_error.value.code == "unsupported_request"


def test_generic_design_with_partial_dimensions_passes_to_audit() -> None:
    """Non-common designs with partial dimensions are handled by the audit LLM, not envelope questions."""
    provider = FakeProvider(
        [
            ready_response(),
            planned_response(
                [
                    {
                        "step_id": 1,
                        "title": "Create part",
                        "description": "Create a part from one supplied dimension.",
                        "category": "primitive",
                        "depends_on": [],
                    }
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    # No common-design keyword and no envelope fallback; goes to audit
    response = service.plan(PlannerRequest(request="Design a custom component with 50 mm length"))

    assert response.status == "planned"
    # Envelope questions are removed per Rule 7; audit handles generic designs
    assert len(provider.calls) == 2  # Audit + planning


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
                        "category": "primitive",
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
                        "category": "primitive",
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
                    "What wall thickness should the object have?",
                    "Wall thickness must fit inside the object diameter.",
                    issue="Wall thickness cannot be greater than or equal to the outer radius.",
                    current_value={"value": 50, "unit": "mm"},
                )
            ]
        )
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            # Use a non-common design with 3 measurements so fallback is empty
            request="Design a 120 mm outer diameter, 50 mm wall thickness, 100 mm height object",
            context={
                "parameter_answers": {
                    "outer_diameter": {"value": 80, "unit": "mm"},
                    "wall_thickness": {"value": 50, "unit": "mm"},
                    "height": {"value": 100, "unit": "mm"},
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
        # Use a request with 3+ measurements so fallback is empty, letting the audit run
        service.plan(PlannerRequest(request="Design a 100 mm by 80 mm by 60 mm object"))


def test_dimension_questions_default_unit_options_for_ui_dropdown() -> None:
    question = parameter_question("side_length", "What side length should the cube have?", "A cube requires one equal side length.")
    question.pop("unit_options")
    service = PlannerService(FakeProvider(needs_parameters_response([question])))

    response = service.plan(PlannerRequest(request="Generate a cube"))

    assert response.status == "needs_parameters"
    # Fallback returns the cube side_length question with default unit_options
    assert response.questions[0].unit_options == ["mm", "cm", "inch"]


def test_needs_parameters_rejects_invalid_question_type() -> None:
    invalid_question = parameter_question("side_length", "What side length should the cube have?", "A side length is required.")
    invalid_question["value_type"] = "linear_dimension"
    service = PlannerService(FakeProvider(needs_parameters_response([invalid_question])))

    with pytest.raises(InvalidModelResponseError):
        # Use a request with 3+ measurements so fallback is empty, letting the audit run
        service.plan(PlannerRequest(request="Design a 100 mm by 80 mm by 60 mm object"))


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
        # Use a request with 3+ measurements so fallback is empty, letting the audit run
        service.plan(PlannerRequest(request="Design a 100 mm by 80 mm by 60 mm object"))


def test_needs_parameters_rejects_mixed_steps_and_questions() -> None:
    response = {
        "status": "needs_parameters",
        "questions": [
            parameter_question("side_length", "What side length should the cube have?", "A side length is required."),
        ],
        "steps": [
            {
                "step_id": 1,
                "title": "Create object",
                "description": "Create the object body.",
                "depends_on": [],
            }
        ],
    }
    service = PlannerService(FakeProvider(json.dumps(response)))

    with pytest.raises(InvalidModelResponseError):
        # Use a request with 3+ measurements so fallback is empty, letting the audit run
        service.plan(PlannerRequest(request="Design a 100 mm by 80 mm by 60 mm object"))


def test_large_request_preserves_ordered_dependencies() -> None:
    steps = [
        {
            "step_id": step_id,
            "title": f"Model assembly feature {step_id}",
            "description": f"Create the required engineering feature number {step_id} for the assembly.",
            "category": "primitive",
            "depends_on": [] if step_id == 1 else [step_id - 1],
        }
        for step_id in range(1, 31)
    ]
    service = PlannerService(FakeProvider([ready_response(), planned_response(steps)]))
    request = PlannerRequest(
        request=(
            "Design a thirty-feature 300 mm by 200 mm by 120 mm industrial assembly "
            "with sequential structural and interface details."
        ),
        context={"expected_design": "Industrial assembly", "completed_steps": [], "remaining_steps": [], "errors": []},
    )

    response = service.plan(request)

    assert len(response.steps) == 30
    assert response.steps[-1].step_id == 30
    assert response.steps[-1].depends_on == [29]


def test_complex_request_returns_hierarchical_phases_with_flattened_steps() -> None:
    """Complex designs return construction phases and a flattened global steps list."""
    provider = FakeProvider(
        [
            ready_response(),
            phased_response(
                [
                    plan_phase(
                        1,
                        [plan_step(1), plan_step(2, depends_on=[1])],
                        title="Envelope",
                        goal="Define the master outer envelope.",
                    ),
                    plan_phase(
                        2,
                        [plan_step(3, depends_on=[2]), plan_step(4, depends_on=[3])],
                        title="Mounting features",
                        goal="Add the mounting bosses and holes.",
                        depends_on=[1],
                    ),
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(
            request=(
                "Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly "
                "with an envelope, bearing seats, and four corner mounting bosses."
            )
        )
    )

    assert response.status == "planned"
    assert [phase.phase_id for phase in response.phases] == [1, 2]
    assert response.phases[0].title == "Envelope"
    assert response.phases[0].goal == "Define the master outer envelope."
    assert response.phases[1].depends_on == [1]
    assert [step.step_id for step in response.steps] == [1, 2, 3, 4]
    assert response.steps[2].depends_on == [2]
    # Flattened steps mirror the phase steps in order
    assert [step.step_id for step in response.steps] == [
        step.step_id for phase in response.phases for step in phase.steps
    ]


def test_simple_request_returns_flat_steps_without_phases() -> None:
    """Simple parts keep the existing flat steps behavior with empty phases."""
    provider = FakeProvider(
        [
            ready_response(),
            planned_response([plan_step(1), plan_step(2, depends_on=[1])]),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(PlannerRequest(request="Generate a cube with side length 40 mm"))

    assert response.status == "planned"
    assert response.phases == []
    assert [step.step_id for step in response.steps] == [1, 2]


def test_phase_ids_must_be_sequential() -> None:
    service = PlannerService(
        FakeProvider(
            [
                ready_response(),
                phased_response(
                    [
                        plan_phase(1, [plan_step(1)]),
                        plan_phase(3, [plan_step(2)]),
                    ]
                ),
            ]
        )
    )

    with pytest.raises(InvalidModelResponseError):
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )


def test_phase_dependencies_reference_only_earlier_phases() -> None:
    service = PlannerService(
        FakeProvider(
            [
                ready_response(),
                phased_response(
                    [
                        plan_phase(1, [plan_step(1)]),
                        plan_phase(2, [plan_step(2)], depends_on=[3]),
                    ]
                ),
            ]
        )
    )

    with pytest.raises(InvalidModelResponseError):
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )


def test_step_ids_must_be_globally_sequential_across_phases() -> None:
    """Steps continue numbering across phase boundaries without gaps or restarts."""
    service = PlannerService(
        FakeProvider(
            [
                ready_response(),
                phased_response(
                    [
                        plan_phase(1, [plan_step(1)]),
                        plan_phase(2, [plan_step(2), plan_step(4)]),
                    ]
                ),
            ]
        )
    )

    with pytest.raises(InvalidModelResponseError):
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )


def test_cross_phase_step_dependencies_are_allowed_on_earlier_steps() -> None:
    """A step in a later phase may depend on a step from an earlier phase."""
    provider = FakeProvider(
        [
            ready_response(),
            phased_response(
                [
                    plan_phase(1, [plan_step(1)]),
                    plan_phase(2, [plan_step(2, depends_on=[1])], depends_on=[1]),
                ]
            ),
        ]
    )
    service = PlannerService(provider)

    response = service.plan(
        PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm two-stage industrial assembly")
    )

    assert response.status == "planned"
    assert response.steps[1].depends_on == [1]


def test_plan_rejects_mixed_flat_steps_and_phases() -> None:
    """A planned response must contain either steps or phases, never both."""
    response = {
        "status": "planned",
        "steps": [plan_step(1)],
        "phases": [plan_phase(1, [plan_step(1)])],
    }
    service = PlannerService(FakeProvider([ready_response(), json.dumps(response)]))

    with pytest.raises(InvalidModelResponseError):
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )


def test_phase_steps_reject_forbidden_implementation_content() -> None:
    """Phase steps are scanned for prohibited implementation content like flat steps."""
    forbidden_step = plan_step(1)
    forbidden_step["description"] = "Create the body using the FreeCAD extrusion API call."
    service = PlannerService(
        FakeProvider(
            [
                ready_response(),
                phased_response([plan_phase(1, [forbidden_step])]),
            ]
        )
    )

    with pytest.raises(InvalidModelResponseError) as captured_error:
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )

    assert captured_error.value.details == {"step_id": 1}


def test_phase_goal_rejects_forbidden_implementation_content() -> None:
    """Phase goals are scanned for prohibited implementation content too."""
    phase = plan_phase(
        1,
        [plan_step(1)],
        goal="Define the envelope using the FreeCAD API before modeling.",
    )
    service = PlannerService(FakeProvider([ready_response(), phased_response([phase])]))

    with pytest.raises(InvalidModelResponseError) as captured_error:
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )

    assert captured_error.value.details == {"phase_id": 1}


def test_phase_requires_at_least_one_step() -> None:
    phase = plan_phase(1, [])
    service = PlannerService(FakeProvider([ready_response(), phased_response([phase])]))

    with pytest.raises(InvalidModelResponseError):
        service.plan(
            PlannerRequest(request="Design a 200 mm by 120 mm by 100 mm multi-feature industrial assembly")
        )
