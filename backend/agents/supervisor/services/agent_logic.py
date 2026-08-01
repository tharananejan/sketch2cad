import os
import json
import logging
import asyncio
from groq import AsyncGroq, GroqError
from deps import Settings, get_settings
from schemas.request import SupervisorRequest
from schemas.response import SupervisorResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are the gateway routing agent for a CAD modeling system (Sketch2CAD). 
Your job is to evaluate the user's instruction and classify it as either "simple" or "complex".

CLASSIFICATION RULES:
- "simple": Route to "simple" ONLY if the user requests creating a SINGLE, standalone basic geometric primitive (e.g., cube, cylinder, sphere, cone, box, torus) with optional basic dimensions.
- "complex": Route to "complex" if the request involves compound shapes, relative positioning ("on top of"), non-CAD objects (trees, eyes, faces, characters), custom mechanical features (brackets, mounting holes), or non-CAD commands.

FEW-SHOT EXAMPLES:
User: "make a cube" -> {"routing_path": "simple"}
User: "create a cylinder 10mm radius" -> {"routing_path": "simple"}
User: "draw a 50mm sphere" -> {"routing_path": "simple"}

User: "Make a cube on top of a tree with eyes" -> {"routing_path": "complex"}
User: "design a bracket with mounting holes" -> {"routing_path": "complex"}
User: "make a cube and a cylinder" -> {"routing_path": "complex"}
User: "cube on top of a cylinder" -> {"routing_path": "complex"}
User: "open the toolbox" -> {"routing_path": "complex"}

You MUST respond with a valid JSON object strictly matching this schema:
{
    "routing_path": "simple" | "complex"
}
"""


async def evaluate_complexity(request: SupervisorRequest, settings: Settings = None) -> SupervisorResponse:
    """
    Evaluates the user instruction using the Groq Cloud LLM to determine routing path.
    - Sketch-only requests route deterministically to 'complex'.
    - Text instructions are evaluated completely by the LLM to choose 'simple' or 'complex'.
    """
    if settings is None:
        settings = get_settings()

    instruction = (request.instruction or "").strip()

    # Sketch-only (no instruction, canvas present) -> Complex
    if not instruction and request.canvas_data:
        return SupervisorResponse(
            routing_path="complex",
            original_instruction=""
        )

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY_SUPERVISOR is not set. Falling back to complex path.")
        return SupervisorResponse(
            routing_path="complex",
            original_instruction=request.instruction
        )

    # Let the LLM choose routing path completely
    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            ),
            timeout=15.0
        )
        llm_content = response.choices[0].message.content
        llm_output = json.loads(llm_content)
        routing_path = llm_output.get("routing_path", "complex")

        if routing_path not in ("simple", "complex"):
            routing_path = "complex"

        return SupervisorResponse(
            routing_path=routing_path,
            original_instruction=request.instruction
        )
    except Exception as e:
        logger.error(f"Supervisor LLM call failed: {e}")
        # Fallback safely to complex path if LLM call fails
        return SupervisorResponse(
            routing_path="complex",
            original_instruction=request.instruction
        )



