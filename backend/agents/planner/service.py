"""Core Frontier Planning Agent orchestration logic."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, TypeVar

from pydantic import ValidationError

from .errors import (
    InvalidModelResponseError,
    InvalidRequestError,
    MalformedModelResponseError,
    UnsupportedRequestError,
)
from .models import (
    DimensionAnswer,
    NeedsParametersResponse,
    ParameterAuditDraft,
    ParameterQuestion,
    PlanDraft,
    PlanPhase,
    PlanResponse,
    PlanStep,
    PlannerRequest,
    PlannerResponse,
)
from .prompts.system_prompt import PLANNER_AUDIT_SYSTEM_PROMPT, PLANNER_PLANNING_SYSTEM_PROMPT
from .providers.base import LLMProvider

_DraftT = TypeVar("_DraftT", ParameterAuditDraft, PlanDraft)

_FORBIDDEN_OUTPUT_PATTERNS = (
    re.compile(r"```", re.IGNORECASE),
    re.compile(r"\bpython\b", re.IGNORECASE),
    re.compile(r"\bfreecad\b", re.IGNORECASE),
    re.compile(r"\bapi\b", re.IGNORECASE),
    re.compile(r"\bimport\s+\w+", re.IGNORECASE),
    re.compile(r"\bdef\s+\w+", re.IGNORECASE),
    re.compile(r"\bhttps?://", re.IGNORECASE),
)

_SUPPORTED_UNITS = {"mm", "cm", "inch"}

# Keyword sets used to detect semantically equivalent parameter IDs across rounds.
# If the LLM returns "outer_diameter" when "body_diameter" is already answered,
# the keyword overlap ("diameter") lets us recognise them as the same concept.
_DIMENSION_KEYWORDS = {
    "diameter", "radius", "height", "width", "length", "depth",
    "thickness", "clearance", "angle", "capacity", "volume",
}

# Parameter IDs matching these patterns are derivable from other parameters and
# should not be asked about. Each entry maps a derivable pattern to a tuple of
# source parameters that must be present for it to be auto-derived.
_DERIVABLE_RULES: list[tuple[set[str], tuple[str, ...]]] = [
    # inner_diameter = outer_diameter - 2 * wall_thickness
    ({"inner", "diameter"}, ("diameter", "wall")),
    ({"interior", "diameter"}, ("diameter", "wall")),
    ({"inner", "radius"}, ("radius", "wall")),
    # body_height = overall_height - neck_height
    ({"body", "height"}, ("height", "neck")),
]


class PlannerService:
    """Produces validated complex CAD modeling plans using an injected provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def plan(self, planner_request: PlannerRequest) -> PlannerResponse:
        """Create one strict modeling plan from a complex request and its context."""

        if not planner_request.request.strip():
            raise InvalidRequestError("The request must not be empty.")

        plan_id = self._derive_plan_id(planner_request)

        # Stage 1: Check unanswered pending questions (from previous rounds)
        pending_questions = self._questions_requiring_answers(
            planner_request.context.pending_questions,
            planner_request.context.parameter_answers,
            ignore_missing=True,
        )
        if pending_questions:
            return NeedsParametersResponse(
                plan_id=plan_id,
                complexity="complex",
                questions=pending_questions,
            )



        # Stage 2: Audit LLM for validation and uncovered parameters
        user_prompt = self._build_user_prompt(planner_request)
        audit_response = self._provider.generate(
            system_prompt=PLANNER_AUDIT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        audit_draft = self._parse_draft(audit_response, ParameterAuditDraft)

        if audit_draft.status == "unsupported":
            raise UnsupportedRequestError(
                audit_draft.reason or "The request is not supported for CAD modeling.",
            )

        if audit_draft.status == "needs_parameters":
            # Deduplicate questions against already-answered parameter IDs
            deduped_questions = self._deduplicate_questions(
                audit_draft.questions,
                planner_request.context.parameter_answers,
            )
            # Filter out questions for derivable parameters
            non_derivable_questions = [
                q for q in deduped_questions
                if not self._is_derivable_question(q, planner_request.context.parameter_answers)
            ]
            unresolved_audit_questions = self._questions_requiring_answers(
                non_derivable_questions,
                planner_request.context.parameter_answers,
            )
            unresolved_audit_questions = self._keep_explicit_correction_questions(
                non_derivable_questions,
                unresolved_audit_questions,
            )
            if not unresolved_audit_questions:
                audit_draft = ParameterAuditDraft(status="ready")
            else:
                return NeedsParametersResponse(
                    plan_id=plan_id,
                    complexity="complex",
                    questions=unresolved_audit_questions,
                )

        plan_response = self._provider.generate(
            system_prompt=PLANNER_PLANNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        plan_draft = self._parse_draft(plan_response, PlanDraft)

        if plan_draft.status == "unsupported":
            raise UnsupportedRequestError(
                plan_draft.reason or "The request is not supported for CAD modeling.",
            )

        self._ensure_modeling_only(plan_draft.steps, plan_draft.phases)
        if plan_draft.phases:
            flattened_steps = [step for phase in plan_draft.phases for step in phase.steps]
            return PlanResponse(
                plan_id=plan_id,
                complexity="complex",
                steps=flattened_steps,
                phases=plan_draft.phases,
            )
        return PlanResponse(
            plan_id=plan_id,
            complexity="complex",
            steps=plan_draft.steps,
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

    def _parse_draft(self, raw_response: str, draft_type: type[_DraftT]) -> _DraftT:
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
            return draft_type.model_validate(payload)
        except ValidationError as error:
            raise InvalidModelResponseError(
                "The planner provider returned JSON outside the planner contract.",
                details={"validation_errors": error.errors(include_url=False)},
            ) from error

    def _questions_requiring_answers(
        self,
        pending_questions: list[ParameterQuestion],
        parameter_answers: dict[str, Any],
        ignore_missing: bool = False,
    ) -> list[ParameterQuestion]:
        unresolved_questions: list[ParameterQuestion] = []
        for question in pending_questions:
            if question.parameter_id not in parameter_answers:
                if ignore_missing:
                    # User skipped this question. Do not block. We will let the LLM assume a default.
                    continue
                unresolved_questions.append(question)
                continue

            answer = parameter_answers[question.parameter_id]
            issue = self._answer_issue(question, answer)
            if issue:
                # If the answer has a valid dimension shape (value + unit),
                # accept it anyway — don't re-ask just because the LLM
                # flagged a cross-parameter concern on a previous round.
                if question.value_type == "dimension":
                    coerced = self._coerce_dimension_answer(answer)
                    if coerced is not None and coerced.unit in _SUPPORTED_UNITS and coerced.value > 0:
                        continue
                unresolved_questions.append(
                    question.model_copy(
                        update={
                            "current_value": answer,
                            "issue": issue,
                        }
                    )
                )
        return unresolved_questions

    @staticmethod
    def _keep_explicit_correction_questions(
        audit_questions: list[ParameterQuestion],
        unresolved_questions: list[ParameterQuestion],
    ) -> list[ParameterQuestion]:
        """Retain model-reported CAD contradictions even when their shape is valid.

        A valid dimension payload only proves that the user selected a positive value and a
        supported unit. An audit may still identify a cross-parameter conflict such as a wall
        thickness that cannot fit inside an outer diameter. Those questions must remain visible.
        """

        unresolved_ids = {question.parameter_id for question in unresolved_questions}
        for question in audit_questions:
            if question.issue and question.parameter_id not in unresolved_ids:
                unresolved_questions.append(question)
                unresolved_ids.add(question.parameter_id)
        return unresolved_questions

    # Well-known contradictory qualifier pairs — these should NOT be merged.
    _CONTRADICTORY_QUALIFIERS = [
        {"neck", "body"},
        {"inner", "outer"},
        {"top", "bottom"},
        {"front", "back"},
        {"left", "right"},
        {"interior", "exterior"},
    ]

    @staticmethod
    def _deduplicate_questions(
        questions: list[ParameterQuestion],
        parameter_answers: dict[str, Any],
    ) -> list[ParameterQuestion]:
        """Drop questions whose parameter_id is a semantic duplicate of an answered key.

        LLMs sometimes generate different snake_case IDs for the same concept across
        audit rounds (e.g., ``body_diameter`` in round 1 and ``outer_diameter`` in
        round 2). This method detects overlap via shared dimension keywords and drops
        the duplicate question when the answered key already covers the concept.

        Uses aggressive merging: if the primary dimension keyword matches, treat as
        duplicate UNLESS the qualifiers form a known contradictory pair (e.g., neck
        vs body, inner vs outer).
        """

        if not parameter_answers:
            return list(questions)

        answered_keyword_sets: dict[str, set[str]] = {
            key: set(key.split("_")) & _DIMENSION_KEYWORDS
            for key in parameter_answers
        }

        unique_questions: list[ParameterQuestion] = []
        for question in questions:
            q_keywords = set(question.parameter_id.split("_")) & _DIMENSION_KEYWORDS
            if not q_keywords:
                unique_questions.append(question)
                continue

            # Check if an answered parameter shares the primary dimension keyword
            is_duplicate = False
            for answered_id, a_keywords in answered_keyword_sets.items():
                if answered_id == question.parameter_id:
                    # Exact match — already handled by _questions_requiring_answers
                    break
                if q_keywords & a_keywords:
                    # Shared keyword (e.g., both contain "diameter") — likely a duplicate.
                    # Only keep as separate if qualifiers form a known contradictory pair.
                    q_qualifiers = set(question.parameter_id.split("_")) - _DIMENSION_KEYWORDS
                    a_qualifiers = set(answered_id.split("_")) - _DIMENSION_KEYWORDS
                    combined = q_qualifiers | a_qualifiers
                    is_contradictory = any(
                        pair <= combined
                        for pair in PlannerService._CONTRADICTORY_QUALIFIERS
                    )
                    if not is_contradictory:
                        is_duplicate = True
                        break
            if not is_duplicate:
                unique_questions.append(question)

        return unique_questions

    @staticmethod
    def _is_derivable_question(
        question: ParameterQuestion,
        parameter_answers: dict[str, Any],
    ) -> bool:
        """Return True if the question asks for a value derivable from existing answers.

        Uses keyword-based heuristics rather than exact ID matching so the filter
        works regardless of the LLM's naming choices.
        """

        q_keywords = set(question.parameter_id.split("_"))
        all_answer_keywords = set()
        for key in parameter_answers:
            all_answer_keywords.update(key.split("_"))

        for derivable_keywords, required_sources in _DERIVABLE_RULES:
            if derivable_keywords <= q_keywords:
                # The question matches a derivable pattern — check if sources exist
                if all(src in all_answer_keywords for src in required_sources):
                    return True
        return False

    @staticmethod
    def _answer_issue(question: ParameterQuestion, answer: Any) -> str | None:
        if question.value_type == "dimension":
            dimension = PlannerService._coerce_dimension_answer(answer)
            if dimension is None:
                return "Dimension answers must include both a numeric value and a unit."
            if dimension.unit not in _SUPPORTED_UNITS:
                return "Dimension unit must be one of mm, cm, or inch."
            if dimension.value <= 0:
                return "Dimension value must be greater than zero."
            return None

        if question.value_type == "number":
            if isinstance(answer, bool) or not isinstance(answer, (int, float)):
                return "Answer must be a number."
            return None

        if question.value_type == "integer":
            if isinstance(answer, bool) or not isinstance(answer, int):
                return "Answer must be an integer."
            return None

        if question.value_type == "boolean":
            if not isinstance(answer, bool):
                return "Answer must be true or false."
            return None

        if question.value_type == "choice":
            if not isinstance(answer, str) or not answer.strip():
                return "Answer must be one of the listed choices."
            if question.options and answer not in question.options:
                return "Answer must match one of the listed choices."
            return None

        if not isinstance(answer, str) or not answer.strip():
            return "Answer must not be empty."
        return None

    @staticmethod
    def _coerce_dimension_answer(answer: Any) -> DimensionAnswer | None:
        if isinstance(answer, DimensionAnswer):
            return answer
        if not isinstance(answer, dict):
            return None
        try:
            return DimensionAnswer.model_validate(answer)
        except ValidationError:
            return None

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
    def _ensure_modeling_only(steps: list[PlanStep], phases: list[PlanPhase] | None = None) -> None:
        all_steps = list(steps)
        for phase in phases or []:
            phase_text = f"{phase.title}\n{phase.goal}"
            for pattern in _FORBIDDEN_OUTPUT_PATTERNS:
                if pattern.search(phase_text):
                    raise InvalidModelResponseError(
                        "The planner provider returned prohibited implementation content.",
                        details={"phase_id": phase.phase_id},
                    )
            all_steps.extend(phase.steps)
        for step in all_steps:
            step_text = f"{step.title}\n{step.description}"
            for pattern in _FORBIDDEN_OUTPUT_PATTERNS:
                if pattern.search(step_text):
                    raise InvalidModelResponseError(
                        "The planner provider returned prohibited implementation content.",
                        details={"step_id": step.step_id},
                    )
