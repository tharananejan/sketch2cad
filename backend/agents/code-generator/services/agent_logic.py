"""
Agent Logic Service
Coordinates RAG retrieval, Ollama SLM querying, prompt formatting,
and code cleaning/validation to generate FreeCAD macros.
"""

import os
import logging
import requests
from typing import Tuple, List

from deps import Settings, get_settings
from services.rag_retriever import retrieve_context
from tools.error_parser import extract_python_code, validate_python_syntax

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = (
    "You are an expert FreeCAD Python scripting engineer. "
    "Translate natural language sequential CAD instructions into clean, executable FreeCAD Python macro commands. "
    "Output ONLY valid Python code."
)


def _load_system_prompt(settings: Settings) -> str:
    """Load system instructions from prompts directory."""
    prompt_path = os.path.join(settings.PROMPTS_DIR, "system_instructions.md")
    try:
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception as e:
        logger.warning(f"Failed to load system_instructions.md: {e}. Using fallback prompt.")
    return FALLBACK_SYSTEM_PROMPT


def generate_cad_code(step: str, settings: Settings = None) -> Tuple[str, List[str]]:
    """
    Generate FreeCAD Python code for a given instruction step using RAG + local SLM.
    Returns:
        tuple[str, list[str]]: (generated_python_code, list_of_rag_sources)
    """
    if settings is None:
        settings = get_settings()

    if not step or not step.strip():
        return "step not available", []

    # 1. Retrieve RAG context
    context_str, sources = retrieve_context(step, settings=settings)

    # If no relevant knowledge retrieved from knowledge base, terminate process with error
    if not context_str:
        logger.warning(f"No relevant RAG knowledge found for step: '{step}'. Terminating with 'step not available'.")
        return "step not available", []

    # 2. Prepare prompts
    system_prompt = _load_system_prompt(settings)
    user_prompt = (
        f"Reference Context from Knowledge Base:\n{context_str}\n\n"
        f"User Instruction Step:\n{step}\n\n"
        f"If the Reference Context contains the knowledge for this step, generate FreeCAD Python macro code. Otherwise output ONLY: step not available"
    )

    # 3. Query Ollama API
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for deterministic code generation
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        raw_output = data.get("message", {}).get("content", "").strip()
    except requests.ConnectionError:
        error_code = (
            "# [ERROR] Cannot connect to local Ollama server.\n"
            f"# Please ensure Ollama is running at {settings.OLLAMA_BASE_URL} with model {settings.LLM_MODEL}.\n"
            f"# Instruction was: {step}"
        )
        return error_code, sources
    except requests.Timeout:
        error_code = "# [ERROR] Ollama generation request timed out.\n" f"# Instruction was: {step}"
        return error_code, sources
    except Exception as e:
        error_code = f"# [ERROR] Ollama API request failed: {str(e)}\n" f"# Instruction was: {step}"
        return error_code, sources

    if not raw_output or "step not available" in raw_output.lower():
        logger.warning(f"LLM indicated step not available for: '{step}'")
        return "step not available", sources

    # 4. Clean and validate code
    cleaned_code = extract_python_code(raw_output)
    if cleaned_code.strip().lower() == "step not available" or "step not available" in cleaned_code.lower():
        return "step not available", sources

    is_valid, syntax_error = validate_python_syntax(cleaned_code)
    if not is_valid:
        logger.warning(f"Generated code has syntax issue: {syntax_error}")
        # Append a comment indicating syntax check warning
        cleaned_code += f"\n\n# WARNING: AST Syntax Check Issue -> {syntax_error}"

    return cleaned_code, sources
