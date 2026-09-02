"""Utility for appending structured error entries to the error-handler log.

Every orchestrator failure is recorded here so that a future error-handling
agent can learn from frequent error patterns.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

_ERROR_LOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "agents"
    / "error-handler"
    / "docs"
    / "error_log.txt"
)


def log_error(
    *,
    agent_state: str,
    user_prompt: str,
    error_message: str,
    generated_code: Optional[str] = None,
) -> None:
    """Append a structured error entry to the persistent error log.

    Parameters
    ----------
    agent_state:
        The orchestrator state in which the error occurred (e.g. ``CODE_GENERATION``).
    user_prompt:
        The original user instruction that triggered the workflow.
    error_message:
        A human-readable description of the error (traceback, API error, etc.).
    generated_code:
        If the error is related to generated code, include the code snippet.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    entry_lines = [
        f"[{timestamp}]",
        f"  State     : {agent_state}",
        f"  Prompt    : {user_prompt}",
        f"  Error     : {error_message}",
    ]
    if generated_code:
        entry_lines.append(f"  Code      :\n{_indent(generated_code, '    ')}")
    entry_lines.append("")  # blank line separator

    entry = "\n".join(entry_lines) + "\n"

    try:
        _ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        # If we can't write the log, don't crash the orchestrator
        pass


def _indent(text: str, prefix: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())
