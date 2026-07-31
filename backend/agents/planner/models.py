"""Typed request and response models for the Frontier Planning Agent."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


DimensionUnit: TypeAlias = Literal["mm", "cm", "inch"]


class DimensionAnswer(BaseModel):
    """Dimension answer with a user-selected unit."""

    model_config = ConfigDict(extra="forbid")

    value: float
    unit: DimensionUnit


ParameterValue: TypeAlias = DimensionAnswer | str | int | float | bool | dict[str, Any]


class PlannerContext(BaseModel):
    """Execution context supplied by the orchestration layer."""

    model_config = ConfigDict(extra="forbid")

    expected_design: str = ""
    completed_steps: list[str] = Field(default_factory=list)
    remaining_steps: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    parameter_answers: dict[str, ParameterValue] = Field(default_factory=dict)
    pending_questions: list["ParameterQuestion"] = Field(default_factory=list)


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
    category: Literal["planning", "sketch", "feature", "boolean", "assembly", "validation", "finish"]
    depends_on: list[int] = Field(default_factory=list)


class PlanPhase(BaseModel):
    """One construction phase containing an ordered sequence of modeling steps.

    Phases are the hierarchical planning unit for complex designs. A phase groups the
    steps required to complete one major independent feature or logical stage of the
    model. Step IDs remain globally sequential across the whole plan so a step in a
    later phase can depend on a step from an earlier phase.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    phase_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    goal: str = Field(min_length=1, max_length=2_000)
    steps: list[PlanStep] = Field(min_length=1)
    depends_on: list[int] = Field(default_factory=list)


class ParameterQuestion(BaseModel):
    """One CAD-critical parameter the planner needs before it can plan safely."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    parameter_id: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=500)
    value_type: Literal["dimension", "number", "integer", "string", "boolean", "choice"]
    unit: str | None = Field(default=None, max_length=50)
    unit_options: list[DimensionUnit] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1, max_length=500)
    required: bool = Field(default=True)
    default: Any | None = None
    current_value: Any | None = None
    issue: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def default_dimension_units(self) -> "ParameterQuestion":
        """Guarantee dimension questions can render the required unit dropdown."""

        if self.value_type == "dimension" and not self.unit_options:
            self.unit_options = ["mm", "cm", "inch"]
        return self


class ParameterAuditDraft(BaseModel):
    """Internal parameter-audit schema required from the LLM provider."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "needs_parameters", "unsupported"]
    questions: list[ParameterQuestion] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_draft(self) -> "ParameterAuditDraft":
        """Enforce a complete audit, parameter question set, or rejection."""

        if self.status == "unsupported":
            if not self.reason or not self.reason.strip():
                raise ValueError("Unsupported responses must include a reason.")
            if self.questions:
                raise ValueError("Unsupported responses cannot include parameter questions.")
            return self

        if self.reason:
            raise ValueError("Only unsupported responses can include a reason.")

        if self.status == "needs_parameters":
            if not self.questions:
                raise ValueError("Parameter question responses must include at least one question.")

            parameter_ids = [question.parameter_id for question in self.questions]
            if len(parameter_ids) != len(set(parameter_ids)):
                raise ValueError("Parameter question IDs must be unique.")
            return self

        if self.questions:
            raise ValueError("Ready responses cannot include parameter questions.")
        return self


class PlanDraft(BaseModel):
    """Internal plan schema required from the LLM provider.

    A planned response carries either a flat ``steps`` list (simple parts) or a
    hierarchical ``phases`` list (complex designs), never both. When phases are
    present, step IDs must remain globally sequential across every phase so the
    flattened public response stays backward compatible.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["planned", "unsupported"]
    steps: list[PlanStep] = Field(default_factory=list)
    phases: list[PlanPhase] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_draft(self) -> "PlanDraft":
        """Enforce a complete flat or hierarchical plan or an explicit rejection."""

        if self.status == "unsupported":
            if not self.reason or not self.reason.strip():
                raise ValueError("Unsupported responses must include a reason.")
            if self.steps or self.phases:
                raise ValueError("Unsupported responses cannot include modeling steps or phases.")
            return self

        if self.reason:
            raise ValueError("Only unsupported responses can include a reason.")
        if not self.steps and not self.phases:
            raise ValueError("Planned responses must include at least one modeling step or construction phase.")
        if self.steps and self.phases:
            raise ValueError("Planned responses cannot mix flat steps with construction phases.")

        if self.phases:
            PlanDraft._validate_phases(self.phases)
            return self

        PlanDraft._validate_steps(self.steps)
        return self

    @staticmethod
    def _validate_steps(steps: list[PlanStep]) -> None:
        """Enforce global sequential IDs and earlier-only dependencies for steps."""

        step_ids = [step.step_id for step in steps]
        expected_ids = list(range(1, len(steps) + 1))
        if step_ids != expected_ids:
            raise ValueError("Step IDs must be sequential integers starting at 1.")

        for step in steps:
            if len(step.depends_on) != len(set(step.depends_on)):
                raise ValueError("A step cannot repeat a dependency.")
            if any(dependency >= step.step_id for dependency in step.depends_on):
                raise ValueError("A step can only depend on earlier steps.")

    @staticmethod
    def _validate_phases(phases: list[PlanPhase]) -> None:
        """Enforce sequential phase IDs, earlier-only phase dependencies, and global step ordering."""

        phase_ids = [phase.phase_id for phase in phases]
        expected_ids = list(range(1, len(phases) + 1))
        if phase_ids != expected_ids:
            raise ValueError("Phase IDs must be sequential integers starting at 1.")

        for phase in phases:
            if len(phase.depends_on) != len(set(phase.depends_on)):
                raise ValueError("A phase cannot repeat a dependency.")
            if any(dependency >= phase.phase_id for dependency in phase.depends_on):
                raise ValueError("A phase can only depend on earlier phases.")

        flattened_steps = [step for phase in phases for step in phase.steps]
        PlanDraft._validate_steps(flattened_steps)


class PlanResponse(BaseModel):
    """Strict public response schema sent to n8n and the code generator.

    ``steps`` always carries the complete flattened, construction-ordered step list so
    downstream consumers keep working unchanged. ``phases`` groups those steps into
    construction phases for complex designs and is empty for simple parts.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["planned"] = "planned"
    plan_id: str = Field(min_length=1)
    complexity: Literal["complex"] = "complex"
    steps: list[PlanStep] = Field(min_length=1)
    phases: list[PlanPhase] = Field(default_factory=list)


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
