import os
import json
import asyncio
from openai import AsyncOpenAI
from schemas.request import SupervisorRequest
from schemas.response import SupervisorResponse

# Configuration for Local Ollama LLM (running at http://localhost:11434)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:0.5b")
LLM_API_KEY = os.getenv("OLLAMA_API_KEY", os.getenv("DEEPSEEK_API_KEY", "ollama"))

def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=OLLAMA_BASE_URL,
    )

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


async def evaluate_complexity(request: SupervisorRequest) -> SupervisorResponse:
    """
    Evaluates the user instruction using the local LLM (Ollama @ http://localhost:11434) to determine routing path.
    - Sketch-only requests route deterministically to 'complex'.
    - Text instructions are evaluated completely by the LLM to choose 'simple' or 'complex'.
    """
    instruction = (request.instruction or "").strip()

    # Sketch-only (no instruction, canvas present) -> Complex
    if not instruction and request.canvas_data:
        return SupervisorResponse(
            routing_path="complex",
            original_instruction=""
        )

    # Let the LLM choose routing path completely
    try:
        client = get_openai_client()
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            ),
            timeout=10.0
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
    except Exception:
        # Fallback safely to complex path if LLM call fails
        return SupervisorResponse(
            routing_path="complex",
            original_instruction=request.instruction
        )


