from backend.agents.supervisor.schemas.request import SupervisorRequest
from backend.agents.supervisor.schemas.response import SupervisorResponse

# The deterministic whitelist of known simple geometric primitives
# Expand this list based on what the Parameter Agent is prepared to handle
SIMPLE_PRIMITIVES = [
    "cube",
    "cylinder",
    "sphere",
    "cone",
    "box",
    "torus"
]

def evaluate_complexity(request: SupervisorRequest) -> SupervisorResponse:
    """
    Evaluates the user instruction to determine the routing path.
    Routes to 'simple' if a primitive is detected, otherwise 'complex'.
    """
    # Normalize the input text for safe matching
    instruction_lower = request.instruction.lower()
    
    # 1. Deterministic Evaluation: Check against the whitelist
    for primitive in SIMPLE_PRIMITIVES:
        if primitive in instruction_lower:
            # Match found! Route down the Simple Path
            return SupervisorResponse(
                routing_path="simple",
                matched_primitive=primitive,
                original_instruction=request.instruction
            )
            
    # 2. Fallback: If no simple primitives are found, route down the Complex Path
    return SupervisorResponse(
        routing_path="complex",
        matched_primitive=None,
        original_instruction=request.instruction
    )