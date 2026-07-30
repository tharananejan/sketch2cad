"""Deterministic FreeCAD subprocess execution for the Sketch2CAD API."""

import json
import re
import subprocess
import threading
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from deps import find_freecad_cli, find_freecad_gui


MODULE_DIR = Path(__file__).resolve().parent
INPUT_PATH = MODULE_DIR / "input.json"
OUTPUT_PATH = MODULE_DIR / "output.json"
TEMP_SCRIPT_PATH = MODULE_DIR / "temp_script.py"
GUI_MACROS_DIRECTORY = MODULE_DIR / "macros"
EXECUTION_TIMEOUT_SECONDS = 60
EXECUTION_LOCK = threading.Lock()
FREECAD_SCRIPT_FAILURE_MARKERS = (
    "Exception while processing file:",
    "Traceback (most recent call last):",
)
FREECAD_PROGRESS_NOISE = re.compile(
    r"(?:saving\.+\n)?(?:[^\n\r]*\(\d{1,3} %\)[^\n\r]*\r)+",
    re.IGNORECASE,
)


def load_input(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and validate the local command-line input contract."""
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
    """Execute one validated FreeCAD script and return the core JSON contract."""
    step_id = payload["step_id"]
    code = payload["code"]

    try:
        with EXECUTION_LOCK:
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
            finally:
                TEMP_SCRIPT_PATH.unlink(missing_ok=True)
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


def execute_and_display(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preflight generated code, then run it in the local FreeCAD GUI window."""
    result = execute(payload)
    if result["status"] == "FAILED":
        return result

    step_id = payload["step_id"]
    try:
        freecad_gui = find_freecad_gui()
        if freecad_gui is None:
            return failed_result(
                step_id,
                result["stdout"],
                "FreeCAD GUI could not be located for model display.",
            )

        GUI_MACROS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        macro_path = GUI_MACROS_DIRECTORY / "step-{}.FCMacro".format(step_id)
        macro_path.write_text(payload["code"], encoding="utf-8")
        subprocess.Popen(
            [freecad_gui, str(macro_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        result["stdout"] = "{}\nOpened the generated model in FreeCAD GUI.".format(
            result["stdout"].rstrip("\n")
        )
        return result
    except OSError:
        return failed_result(step_id, result["stdout"], traceback.format_exc())
    except Exception:
        return failed_result(step_id, result["stdout"], traceback.format_exc())


def write_output(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Write the local command-line result contract as JSON."""
    if output_path is None:
        output_path = OUTPUT_PATH
    output_path.write_text(
        json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    """Run the compatibility command-line contract and display its model."""
    write_output(execute_and_display(load_input()))


if __name__ == "__main__":
    main()
