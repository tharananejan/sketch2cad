import re

from schemas.request import SupervisorRequest
from schemas.response import SupervisorResponse

# The deterministic whitelist of known simple geometric primitives
# Expand this list based on what the Parameter Agent is prepared to handle
SIMPLE_PRIMITIVES = [
    "cube",
    "cylinder",
    "sphere",
    "cone",
    "box",
    "torus",
]

_PRIMITIVE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in SIMPLE_PRIMITIVES) + r")\b",
    re.IGNORECASE,
)


def _has_canvas_data(request: SupervisorRequest) -> bool:
    """Return True when a non-empty tldraw sketch payload is present."""
    return bool(request.canvas_data)


def evaluate_complexity(request: SupervisorRequest) -> SupervisorResponse:
    """
    Evaluates the user instruction to determine the routing path.
    Routes to 'simple' if a whitelisted primitive is detected (word-boundary match),
    otherwise 'complex' (unmatched text, sketch-only, or sketch + complex text).
    """
    instruction = request.instruction or ""
    match = _PRIMITIVE_PATTERN.search(instruction)

    if match:
        return SupervisorResponse(
            routing_path="simple",
            matched_primitive=match.group(1).lower(),
            original_instruction=instruction,
        )

    # No whitelist hit → complex. Covers unmatched text and sketch-only
    # payloads (where _has_canvas_data is True and instruction is empty).
    return SupervisorResponse(
        routing_path="complex",
        matched_primitive=None,
        original_instruction=instruction,
    )
