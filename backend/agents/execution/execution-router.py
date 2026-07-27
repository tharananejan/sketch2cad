"""Run generated FreeCAD scripts in a deterministic headless subprocess."""

import json
import re
import subprocess
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from deps import find_freecad_cli


MODULE_DIR = Path(__file__).resolve().parent
INPUT_PATH = MODULE_DIR / "input.json"
OUTPUT_PATH = MODULE_DIR / "output.json"
TEMP_SCRIPT_PATH = MODULE_DIR / "temp_script.py"
EXECUTION_TIMEOUT_SECONDS = 60
FREECAD_SCRIPT_FAILURE_MARKERS = (
    "Exception while processing file:",
    "Traceback (most recent call last):",
)
FREECAD_PROGRESS_NOISE = re.compile(
    r"(?:saving\.+\n)?(?:[^\n\r]*\(\d{1,3} %\)[^\n\r]*\r)+",
    re.IGNORECASE,
)


def load_input(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and validate the execution agent's input contract."""
    if input_path is None:
        input_path = INPUT_PATH

    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("input.json must contain a JSON object.")

    if type(payload.get("step_id")) is not int:
        raise ValueError("input.json field 'step_id' must be an integer.")

    if not isinstance(payload.get("code"), str):
        raise ValueError("input.json field 'code' must be a string.")

    return payload


def decode_captured_output(data: Any) -> str:
    """Decode process bytes without changing line endings or text content."""
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="surrogateescape")
    if isinstance(data, str):
        return data
    raise TypeError("Captured process output must be bytes, text, or None.")


def clean_stdout(stdout: str) -> str:
    """Remove terminal-style FreeCAD progress updates from captured stdout."""
    return FREECAD_PROGRESS_NOISE.sub("", stdout)


def failed_result(step_id: int, stdout: str, error_trace: str) -> Dict[str, Any]:
    """Build an output object that conforms to the failure contract."""
    return {
        "step_id": step_id,
        "status": "FAILED",
        "stdout": stdout,
        "error_trace": error_trace,
    }


def has_freecad_script_failure(error_trace: str) -> bool:
    """Return whether FreeCAD reported an explicit script execution failure."""
    return any(marker in error_trace for marker in FREECAD_SCRIPT_FAILURE_MARKERS)


def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one validated script and return the structured result."""
    step_id = payload["step_id"]
    code = payload["code"]

    try:
        freecad_cli = find_freecad_cli()
        if freecad_cli is None:
            return failed_result(
                step_id,
                "",
                "FreeCAD CLI could not be located via FREECAD_PATH, PATH, or standard installation paths.",
            )

        TEMP_SCRIPT_PATH.write_text(code, encoding="utf-8")
        completed = subprocess.run(
            [freecad_cli, str(TEMP_SCRIPT_PATH)],
            capture_output=True,
            check=False,
            shell=False,
            timeout=EXECUTION_TIMEOUT_SECONDS,
        )

        stdout = clean_stdout(decode_captured_output(completed.stdout))
        stderr = decode_captured_output(completed.stderr)
        if completed.returncode == 0:
            if has_freecad_script_failure(stderr):
                return failed_result(step_id, stdout, stderr)

            return {
                "step_id": step_id,
                "status": "SUCCESS",
                "stdout": stdout,
                "error_trace": None,
            }

        return failed_result(step_id, stdout, stderr)
    except subprocess.TimeoutExpired as error:
        stdout = clean_stdout(decode_captured_output(error.output))
        stderr = decode_captured_output(error.stderr)
        return failed_result(
            step_id,
            stdout,
            stderr
            or "Execution timed out after {} seconds.".format(
                EXECUTION_TIMEOUT_SECONDS
            ),
        )
    except OSError:
        return failed_result(step_id, "", traceback.format_exc())
    except Exception:
        return failed_result(step_id, "", traceback.format_exc())
    finally:
        TEMP_SCRIPT_PATH.unlink(missing_ok=True)


def write_output(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Write the exact output contract using an ASCII-safe JSON encoding."""
    if output_path is None:
        output_path = OUTPUT_PATH

    output_path.write_text(
        json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    """Read the contract, execute the script, and emit output.json."""
    payload = load_input()
    write_output(execute(payload))


if __name__ == "__main__":
    main()
