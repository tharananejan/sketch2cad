"""Typed request and response models for the Frontier Planning Agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlannerContext(BaseModel):
    """Execution context supplied by the orchestration layer."""

    model_config = ConfigDict(extra="forbid")

    expected_design: str = ""
    completed_steps: list[str] = Field(default_factory=list)
    remaining_steps: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


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


class PlanDraft(BaseModel):
    """Internal response schema required from the LLM provider."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["planned", "unsupported"]
    steps: list[PlanStep] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_draft(self) -> "PlanDraft":
        """Enforce a complete sequential plan or an explicit rejection."""

        if self.status == "unsupported":
            if not self.reason or not self.reason.strip():
                raise ValueError("Unsupported responses must include a reason.")
            if self.steps:
                raise ValueError("Unsupported responses cannot include modeling steps.")
            return self

        if not self.steps:
            raise ValueError("Planned responses must include at least one modeling step.")

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

    plan_id: str = Field(min_length=1)
    complexity: Literal["complex"] = "complex"
    steps: list[PlanStep] = Field(min_length=1)
