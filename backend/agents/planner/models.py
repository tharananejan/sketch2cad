"""Typed request and response models for the Frontier Planning Agent."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


ParameterValue: TypeAlias = str | int | float | bool


class PlannerContext(BaseModel):
    """Execution context supplied by the orchestration layer."""

    model_config = ConfigDict(extra="forbid")

    expected_design: str = ""
    completed_steps: list[str] = Field(default_factory=list)
    remaining_steps: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    parameter_answers: dict[str, ParameterValue] = Field(default_factory=dict)


class PlannerRequest(BaseModel):
    """Complex request accepted by the planner endpoint."""

    model_config = ConfigDict(extra="forbid")

    request: str
    context: PlannerContext = Field(default_factory=PlannerContext)


class PlanStep(BaseModel):
    """One sequential, implementation-agnostic CAD modeling operation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    step_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)
    depends_on: list[int] = Field(default_factory=list)


class ParameterQuestion(BaseModel):
    """One CAD-critical parameter the planner needs before it can plan safely."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    parameter_id: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=500)
    value_type: Literal["number", "integer", "string", "boolean", "choice"]
    unit: str | None = Field(default=None, max_length=50)
    options: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1, max_length=500)


class PlanDraft(BaseModel):
    """Internal response schema required from the LLM provider."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["planned", "needs_parameters", "unsupported"]
    steps: list[PlanStep] = Field(default_factory=list)
    questions: list[ParameterQuestion] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_draft(self) -> "PlanDraft":
        """Enforce a complete sequential plan or an explicit rejection."""

        if self.status == "unsupported":
            if not self.reason or not self.reason.strip():
                raise ValueError("Unsupported responses must include a reason.")
            if self.steps:
                raise ValueError("Unsupported responses cannot include modeling steps.")
            if self.questions:
                raise ValueError("Unsupported responses cannot include parameter questions.")
            return self

        if self.reason:
            raise ValueError("Only unsupported responses can include a reason.")

        if self.status == "needs_parameters":
            if self.steps:
                raise ValueError("Parameter question responses cannot include modeling steps.")
            if not self.questions:
                raise ValueError("Parameter question responses must include at least one question.")

            parameter_ids = [question.parameter_id for question in self.questions]
            if len(parameter_ids) != len(set(parameter_ids)):
                raise ValueError("Parameter question IDs must be unique.")
            return self

        if not self.steps:
            raise ValueError("Planned responses must include at least one modeling step.")
        if self.questions:
            raise ValueError("Planned responses cannot include parameter questions.")

        step_ids = [step.step_id for step in self.steps]
        expected_ids = list(range(1, len(self.steps) + 1))
        if step_ids != expected_ids:
            raise ValueError("Step IDs must be sequential integers starting at 1.")

        for step in self.steps:
            if len(step.depends_on) != len(set(step.depends_on)):
                raise ValueError("A step cannot repeat a dependency.")
            if any(dependency >= step.step_id for dependency in step.depends_on):
                raise ValueError("A step can only depend on earlier steps.")
        return self


class PlanResponse(BaseModel):
    """Strict public response schema sent to n8n and the code generator."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["planned"] = "planned"
    plan_id: str = Field(min_length=1)
    complexity: Literal["complex"] = "complex"
    steps: list[PlanStep] = Field(min_length=1)


class NeedsParametersResponse(BaseModel):
    """Public response asking orchestration to collect missing CAD parameters."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["needs_parameters"] = "needs_parameters"
    plan_id: str = Field(min_length=1)
    complexity: Literal["complex"] = "complex"
    questions: list[ParameterQuestion] = Field(min_length=1)


PlannerResponse: TypeAlias = Annotated[
    PlanResponse | NeedsParametersResponse,
    Field(discriminator="status"),
]
