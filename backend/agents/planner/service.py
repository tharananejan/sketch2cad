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
_LINEAR_UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mm|millimeter|millimeters|cm|centimeter|centimeters|in|inch|inches)\b",
    re.IGNORECASE,
)
_VOLUME_UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ml|milliliter|milliliters|l|liter|liters|oz|ounce|ounces)\b",
    re.IGNORECASE,
)
_NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b", re.IGNORECASE)
_DIMENSION_KEYWORDS = (
    "height",
    "tall",
    "width",
    "wide",
    "depth",
    "deep",
    "length",
    "long",
    "diameter",
    "radius",
    "thickness",
    "clearance",
    "slot",
    "lip",
    "side",
)
_ANGLE_KEYWORDS = ("angle", "tilt", "incline", "lean", "degrees", "degree")
_SUPPORTED_UNITS = {"mm", "cm", "inch"}


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
        )
        if pending_questions:
            return NeedsParametersResponse(
                plan_id=plan_id,
                complexity="complex",
                questions=pending_questions,
            )

        # Stage 2: Deterministic parameter questions (reliable, always consistent)
        # Runs BEFORE the audit so known designs always get the right questions.
        deterministic_questions = self._deterministic_parameter_questions(planner_request)
        if deterministic_questions:
            unresolved = self._questions_requiring_answers(
                deterministic_questions,
                planner_request.context.parameter_answers,
            )
            if unresolved:
                return NeedsParametersResponse(
                    plan_id=plan_id,
                    complexity="complex",
                    questions=unresolved,
                )

        # Stage 3: Audit LLM for validation and uncovered parameters
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
            unresolved_audit_questions = self._questions_requiring_answers(
                audit_draft.questions,
                planner_request.context.parameter_answers,
            )
            unresolved_audit_questions = self._keep_explicit_correction_questions(
                audit_draft.questions,
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

        self._ensure_modeling_only(plan_draft.steps)
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
    ) -> list[ParameterQuestion]:
        unresolved_questions: list[ParameterQuestion] = []
        for question in pending_questions:
            if question.parameter_id not in parameter_answers:
                unresolved_questions.append(question)
                continue

            answer = parameter_answers[question.parameter_id]
            issue = self._answer_issue(question, answer)
            if issue:
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

    def _deterministic_parameter_questions(
        self,
        planner_request: PlannerRequest,
    ) -> list[ParameterQuestion]:
        """Generate deterministic parameter questions for underspecified designs.

        Runs before the audit to ensure known designs (cube, mug, bottle, etc.)
        always get the right questions regardless of LLM consistency.
        """

        request_text = planner_request.request.lower()
        answered_parameter_ids = set(planner_request.context.parameter_answers)

        unitless_questions = self._unitless_dimension_questions(request_text)
        if unitless_questions:
            return unitless_questions

        common_questions = self._common_design_missing_questions(request_text, answered_parameter_ids)
        if common_questions:
            return common_questions
        if self._is_common_design(request_text):
            return []

        if not planner_request.context.parameter_answers:
            generic_questions = self._generic_envelope_questions(request_text)
            if generic_questions:
                return generic_questions

        return []

    def _unitless_dimension_questions(self, request_text: str) -> list[ParameterQuestion]:
        questions: list[ParameterQuestion] = []
        for index, match in enumerate(_NUMBER_PATTERN.finditer(request_text), start=1):
            number_text = match.group(0)
            window_start = max(0, match.start() - 35)
            window_end = min(len(request_text), match.end() + 35)
            window = request_text[window_start:window_end]
            if _LINEAR_UNIT_PATTERN.search(window) or "degree" in window:
                continue
            if not any(keyword in window for keyword in _DIMENSION_KEYWORDS):
                continue

            questions.append(
                self._dimension_question(
                    self._parameter_id_from_window(window, index),
                    "This dimension is missing a unit. What corrected value and unit should it use?",
                    "The planner cannot choose whether a dimension is mm, cm, or inch.",
                    current_value=float(number_text) if "." in number_text else int(number_text),
                    issue="Dimension is missing a unit.",
                )
            )
        return questions

    def _generic_envelope_questions(self, request_text: str) -> list[ParameterQuestion]:
        measurement_count = self._linear_measurement_count(request_text)
        if measurement_count >= 3:
            return []

        if measurement_count == 2:
            return [
                self._dimension_question(
                    "overall_height",
                    "What overall height should this design use?",
                    "A code-ready CAD plan needs the missing main envelope dimension.",
                )
            ]

        if measurement_count == 1:
            return [
                self._dimension_question(
                    "overall_width",
                    "What overall width should this design use?",
                    "A single supplied dimension is not enough for a code-ready CAD plan.",
                ),
                self._dimension_question(
                    "overall_height",
                    "What overall height should this design use?",
                    "A single supplied dimension is not enough for a code-ready CAD plan.",
                ),
            ]

        return [
            self._dimension_question(
                "overall_length",
                "What overall length should this design use?",
                "A code-ready CAD plan needs at least the main envelope dimensions.",
            ),
            self._dimension_question(
                "overall_width",
                "What overall width should this design use?",
                "A code-ready CAD plan needs at least the main envelope dimensions.",
            ),
            self._dimension_question(
                "overall_height",
                "What overall height should this design use?",
                "A code-ready CAD plan needs at least the main envelope dimensions.",
            ),
        ]

    def _common_design_missing_questions(
        self,
        request_text: str,
        answered_parameter_ids: set[str],
    ) -> list[ParameterQuestion]:
        if "cube" in request_text:
            if "side_length" not in answered_parameter_ids and not self._has_linear_measurement(request_text):
                return [
                    self._dimension_question(
                        "side_length",
                        "What side length should the cube have?",
                        "A cube requires one equal side length before CAD planning.",
                    )
                ]
            return []

        if "sphere" in request_text or "ball" in request_text:
            if not ({"sphere_radius", "sphere_diameter"} & answered_parameter_ids) and not self._has_linear_measurement(
                request_text
            ):
                return [
                    self._dimension_question(
                        "sphere_diameter",
                        "What diameter should the sphere have?",
                        "A sphere requires a radius or diameter before CAD planning.",
                    )
                ]
            return []

        if "cylinder" in request_text:
            return self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "cylinder_diameter",
                        ("diameter", "radius", "wide", "width"),
                        "What diameter should the cylinder have?",
                        "The cylinder needs a circular size before CAD planning.",
                    ),
                    (
                        "cylinder_height",
                        ("height", "tall"),
                        "What height should the cylinder have?",
                        "The cylinder needs a height before CAD planning.",
                    ),
                ],
            )

        if "mug" in request_text or "coffee cup" in request_text or "cup" in request_text:
            return self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "mug_height",
                        ("height", "tall"),
                        "What height should the mug be?",
                        "The mug body height defines the vessel volume.",
                    ),
                    (
                        "outer_diameter",
                        ("diameter", "outer", "wide", "width"),
                        "What outside diameter should the mug have?",
                        "The outside diameter defines the mug body footprint.",
                    ),
                    (
                        "wall_thickness",
                        ("wall", "thickness"),
                        "What wall thickness should the mug have?",
                        "Wall thickness is required to make the mug hollow and manufacturable.",
                    ),
                    (
                        "handle_clearance",
                        ("handle clearance", "finger clearance", "handle opening"),
                        "What handle clearance should the mug provide?",
                        "Handle clearance controls the functional opening for the user's hand.",
                    ),
                ],
            )

        if "phone holder" in request_text or ("phone" in request_text and "holder" in request_text):
            questions = self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "phone_width",
                        ("phone width", "width", "wide"),
                        "What phone width should the holder fit?",
                        "The slot width must match the phone.",
                    ),
                    (
                        "phone_thickness",
                        ("phone thickness", "thickness"),
                        "What phone thickness should the slot accept?",
                        "The slot gap must fit the phone thickness.",
                    ),
                    (
                        "slot_depth",
                        ("slot depth", "depth"),
                        "What slot depth should hold the phone?",
                        "Slot depth controls how securely the phone sits in the holder.",
                    ),
                    (
                        "front_lip_height",
                        ("front lip", "lip height", "lip"),
                        "What front lip height should retain the phone?",
                        "The front lip prevents the phone from sliding out.",
                    ),
                    (
                        "charging_cable_clearance",
                        ("charging", "cable", "clearance"),
                        "What charging-cable clearance should the holder leave?",
                        "Cable clearance affects the functional cutout under the phone.",
                    ),
                ],
            )
            if "holder_angle" not in answered_parameter_ids and not self._has_number_near_keywords(request_text, _ANGLE_KEYWORDS):
                questions.append(
                    ParameterQuestion(
                        parameter_id="holder_angle",
                        question="What viewing angle should the holder use?",
                        value_type="number",
                        unit="degrees",
                        options=[],
                        reason="The support angle sets the phone tilt.",
                    )
                )
            return questions

        if "bottle" in request_text:
            questions = self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "bottle_height",
                        ("height", "tall"),
                        "What overall height should the bottle have?",
                        "The bottle height is a key dimension for shape and capacity calculations.",
                    ),
                    (
                        "body_diameter",
                        ("body diameter", "diameter", "outer", "wide", "width"),
                        "What body diameter should the bottle have?",
                        "The main body diameter defines the bottle's main shape and volume.",
                    ),
                    (
                        "neck_diameter",
                        ("neck diameter", "neck", "top diameter", "mouth"),
                        "What neck diameter should the bottle have?",
                        "The neck diameter is smaller than the body diameter and defines the opening.",
                    ),
                    (
                        "neck_height",
                        ("neck height",),
                        "What neck height should the bottle have?",
                        "The neck height defines the top vertical section before the body transition.",
                    ),
                    (
                        "wall_thickness",
                        ("wall", "thickness"),
                        "What wall thickness should the bottle have?",
                        "Wall thickness is required to calculate the internal cavity and maintain capacity.",
                    ),
                ],
            )
            if "target_capacity" not in answered_parameter_ids and not self._has_volume_measurement(request_text):
                questions.append(
                    ParameterQuestion(
                        parameter_id="target_capacity",
                        question="What target capacity (volume) should the bottle hold?",
                        value_type="number",
                        unit="ml",
                        options=[],
                        reason="The target capacity is required to calculate the internal volume and maintain it.",
                    )
                )
            return questions

        if "enclosure" in request_text or "housing" in request_text:
            return self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "enclosure_width",
                        ("width", "wide"),
                        "What width should the enclosure have?",
                        "The enclosure width defines the main horizontal dimension.",
                    ),
                    (
                        "enclosure_height",
                        ("height", "tall"),
                        "What height should the enclosure have?",
                        "The enclosure height defines the vertical dimension.",
                    ),
                    (
                        "enclosure_depth",
                        ("depth", "deep"),
                        "What depth should the enclosure have?",
                        "The enclosure depth defines the second horizontal dimension.",
                    ),
                    (
                        "wall_thickness",
                        ("wall", "thickness"),
                        "What wall thickness should the enclosure use?",
                        "Wall thickness determines the structural strength and print time.",
                    ),
                    (
                        "corner_radius",
                        ("corner", "radius", "fillet"),
                        "What corner radius should the enclosure use?",
                        "Corner radius affects aesthetics and printability.",
                    ),
                ],
            )

        if "bracket" in request_text:
            return self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "bracket_width",
                        ("width", "wide"),
                        "What width should the bracket have?",
                        "The bracket width defines the primary horizontal span.",
                    ),
                    (
                        "bracket_height",
                        ("height", "tall"),
                        "What height should the bracket have?",
                        "The bracket height defines the vertical leg length.",
                    ),
                    (
                        "bracket_thickness",
                        ("thickness",),
                        "What material thickness should the bracket use?",
                        "Material thickness determines the bracket's load capacity.",
                    ),
                    (
                        "mounting_hole_diameter",
                        ("mounting hole", "hole", "screw"),
                        "What mounting hole diameter should the bracket use?",
                        "Hole diameter must match the fastener size.",
                    ),
                    (
                        "hole_spacing",
                        ("hole spacing", "spacing", "pitch"),
                        "What hole spacing should the bracket use?",
                        "Spacing between mounting holes determines compatibility.",
                    ),
                ],
            )

        if "box" in request_text:
            return self._missing_dimension_questions(
                request_text,
                answered_parameter_ids,
                [
                    (
                        "box_width",
                        ("width", "wide"),
                        "What interior width should the box have?",
                        "The box width defines the primary horizontal dimension.",
                    ),
                    (
                        "box_depth",
                        ("depth", "deep"),
                        "What interior depth should the box have?",
                        "The box depth defines the second horizontal dimension.",
                    ),
                    (
                        "box_height",
                        ("height", "tall"),
                        "What interior height should the box have?",
                        "The box height defines the vertical dimension and usable volume.",
                    ),
                    (
                        "wall_thickness",
                        ("wall", "thickness"),
                        "What wall thickness should the box use?",
                        "Wall thickness determines the structural strength of the box.",
                    ),
                ],
            )

        return []

    @staticmethod
    def _is_common_design(request_text: str) -> bool:
        return (
            "cube" in request_text
            or "sphere" in request_text
            or "ball" in request_text
            or "cylinder" in request_text
            or "mug" in request_text
            or "coffee cup" in request_text
            or "cup" in request_text
            or "phone holder" in request_text
            or ("phone" in request_text and "holder" in request_text)
            or "bottle" in request_text
            or "enclosure" in request_text
            or "housing" in request_text
            or "bracket" in request_text
            or "box" in request_text
        )

    def _missing_dimension_questions(
        self,
        request_text: str,
        answered_parameter_ids: set[str],
        specs: list[tuple[str, tuple[str, ...], str, str]],
    ) -> list[ParameterQuestion]:
        questions: list[ParameterQuestion] = []
        for parameter_id, keywords, question, reason in specs:
            if parameter_id in answered_parameter_ids:
                continue
            if self._has_linear_measurement_near_keywords(request_text, keywords):
                continue
            questions.append(self._dimension_question(parameter_id, question, reason))
        return questions

    @staticmethod
    def _dimension_question(
        parameter_id: str,
        question: str,
        reason: str,
        *,
        current_value: Any | None = None,
        issue: str | None = None,
    ) -> ParameterQuestion:
        return ParameterQuestion(
            parameter_id=parameter_id,
            question=question,
            value_type="dimension",
            unit=None,
            unit_options=["mm", "cm", "inch"],
            options=[],
            reason=reason,
            current_value=current_value,
            issue=issue,
        )

    @staticmethod
    def _has_linear_measurement(request_text: str) -> bool:
        return bool(_LINEAR_UNIT_PATTERN.search(request_text))

    @staticmethod
    def _has_volume_measurement(request_text: str) -> bool:
        return bool(_VOLUME_UNIT_PATTERN.search(request_text))

    @staticmethod
    def _linear_measurement_count(request_text: str) -> int:
        return len(_LINEAR_UNIT_PATTERN.findall(request_text))

    @staticmethod
    def _has_linear_measurement_near_keywords(request_text: str, keywords: tuple[str, ...]) -> bool:
        for match in _LINEAR_UNIT_PATTERN.finditer(request_text):
            window_start = max(0, match.start() - 45)
            window_end = min(len(request_text), match.end() + 45)
            window = request_text[window_start:window_end]
            if any(keyword in window for keyword in keywords):
                return True
        return False

    @staticmethod
    def _has_number_near_keywords(request_text: str, keywords: tuple[str, ...]) -> bool:
        for match in _NUMBER_PATTERN.finditer(request_text):
            window_start = max(0, match.start() - 35)
            window_end = min(len(request_text), match.end() + 35)
            window = request_text[window_start:window_end]
            if any(keyword in window for keyword in keywords):
                return True
        return False

    @staticmethod
    def _parameter_id_from_window(window: str, index: int) -> str:
        if "side" in window:
            return "side_length"
        if "height" in window or "tall" in window:
            return "height"
        if "width" in window or "wide" in window:
            return "width"
        if "depth" in window or "deep" in window:
            return "depth"
        if "diameter" in window:
            return "diameter"
        if "radius" in window:
            return "radius"
        if "thickness" in window:
            return "thickness"
        if "clearance" in window:
            return "clearance"
        return f"dimension_{index}"

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
