"""
Agent Logic Service
Coordinates RAG retrieval, Ollama SLM querying, prompt formatting,
and code cleaning/validation to generate FreeCAD macros.
"""

import os
import json
import logging
from typing import Tuple, List, Union
from groq import Groq, GroqError

from deps import Settings, get_settings
from services.rag_retriever import retrieve_context
from tools.error_parser import validate_python_syntax

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


def generate_cad_code(step: str, settings: Settings = None) -> Tuple[Union[List[str], str], List[str]]:
    """
    Generate FreeCAD Python code for a given instruction step using RAG + local SLM.
    Returns:
        tuple[list[str] | str, list[str]]: (generated_python_code_array, list_of_rag_sources)
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
        f"If the Reference Context contains the knowledge for this step, generate FreeCAD Python macro code. Otherwise output ONLY a JSON object with an error key: {{\"error\": \"step not available\"}}"
    )

    # 3. Query Groq API
    if not settings.GROQ_API_KEY:
        error_code = (
            "# [ERROR] GROQ_API_KEY is not set.\n"
            "# Please set the GROQ_API_KEY environment variable.\n"
            f"# Instruction was: {step}"
        )
        return error_code, sources

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=settings.LLM_MODEL,
            temperature=0.1,  # Low temperature for deterministic code generation
            timeout=120,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        raw_output = chat_completion.choices[0].message.content.strip()
    except GroqError as e:
        error_code = f"# [ERROR] Groq API error: {str(e)}\n" f"# Instruction was: {step}"
        return error_code, sources
    except Exception as e:
        error_code = f"# [ERROR] Generation request failed: {str(e)}\n" f"# Instruction was: {step}"
        return error_code, sources

    if not raw_output or "step not available" in raw_output.lower():
        logger.warning(f"LLM indicated step not available for: '{step}'")
        return "step not available", sources

    # 4. Parse JSON
    try:
        parsed = json.loads(raw_output)
        if "error" in parsed:
            return parsed["error"], sources
        code_array = parsed.get("code", [])
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON from LLM: {raw_output}")
        return "step not available", sources
        
    if not code_array:
        return "step not available", sources

    # Join the array to validate syntax
    full_code = "\n".join(code_array)
    is_valid, syntax_error = validate_python_syntax(full_code)
    if not is_valid:
        logger.warning(f"Generated code has syntax issue: {syntax_error}")
        code_array.append(f"\n# WARNING: AST Syntax Check Issue -> {syntax_error}")

    return code_array, sources
