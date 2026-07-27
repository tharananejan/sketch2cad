"""
Error and Code Parser Utility
Extracts clean Python code from raw SLM markdown outputs and validates syntax using AST.
"""

import re
import ast
from typing import Tuple, Optional


def extract_python_code(raw_text: str) -> str:
    """
    Extract clean Python code from LLM response.
    Strips markdown code fences (```python ... ```) if present.
    """
    if not raw_text:
        return ""

    # Look for ```python ... ``` or ``` ... ``` blocks
    pattern = r"```(?:python)?\s*\n(.*?)\n```"
    matches = re.findall(pattern, raw_text, re.DOTALL | re.IGNORECASE)

    if matches:
        # Join multiple code blocks if the model generated sequential snippets
        return "\n\n".join(m.strip() for m in matches)

    # If no markdown fences found, check if code starts/ends with stray ``` and clean it
    cleaned = re.sub(r"^```(?:python)?", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())

    return cleaned.strip()


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate whether the string is syntactically valid Python code using ast.parse.
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "Generated code is empty."

    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        error_msg = f"SyntaxError on line {e.lineno}: {e.msg}\nLine: {e.text}"
        return False, error_msg
    except Exception as e:
        return False, f"Validation error: {str(e)}"
