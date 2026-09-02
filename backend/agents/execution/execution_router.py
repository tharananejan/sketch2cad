"""Run generated code in one persistent FreeCAD GUI document."""

import json
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from deps import find_freecad_gui


MODULE_DIR = Path(__file__).resolve().parent
INPUT_PATH = MODULE_DIR / "input.json"
OUTPUT_PATH = MODULE_DIR / "output.json"
GUI_MACROS_DIRECTORY = MODULE_DIR / "macros"
GUI_BRIDGE_TEMPLATE_PATH = MODULE_DIR / "freecad_gui_bridge.FCMacro.template"
GUI_BRIDGE_MACRO_PATH = GUI_MACROS_DIRECTORY / "sketch2cad_session.FCMacro"
PROJECT_DOCUMENT_PATH = MODULE_DIR / "models" / "sketch2cad.FCStd"
EXECUTION_TIMEOUT_SECONDS = 60
GUI_START_TIMEOUT_SECONDS = 20
GUI_BRIDGE_HOST = "127.0.0.1"
GUI_BRIDGE_PORT = 49217
EXECUTION_LOCK = threading.Lock()


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


def failed_result(step_id: int, stdout: str, error_trace: str) -> Dict[str, Any]:
    """Build an output object that conforms to the failure contract."""
    return {
        "step_id": step_id,
        "status": "FAILED",
        "stdout": stdout,
        "error_trace": error_trace,
    }


def _send_gui_bridge_request(request: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """Send one JSON request to the FreeCAD GUI bridge and read its response."""
    encoded_request = (json.dumps(request, ensure_ascii=True) + "\n").encode("utf-8")
    with socket.create_connection((GUI_BRIDGE_HOST, GUI_BRIDGE_PORT), timeout=timeout) as connection:
        connection.settimeout(timeout)
        connection.sendall(encoded_request)
        response = b""
        while not response.endswith(b"\n"):
            chunk = connection.recv(65536)
            if not chunk:
                raise ConnectionError("FreeCAD GUI bridge closed the connection without a response.")
            response += chunk

    decoded_response = response.decode("utf-8")
    payload = json.loads(decoded_response)
    if not isinstance(payload, dict):
        raise ValueError("FreeCAD GUI bridge returned an invalid response.")
    return payload


def _gui_bridge_is_ready() -> bool:
    """Return whether the managed FreeCAD GUI session is ready to execute code."""
    try:
        response = _send_gui_bridge_request({"action": "health"}, timeout=0.25)
        return response == {
            "status": "READY",
            "project_document_path": str(PROJECT_DOCUMENT_PATH),
        }
    except (ConnectionError, OSError, ValueError, json.JSONDecodeError, socket.timeout):
        return False


def _write_gui_bridge_macro() -> None:
    """Materialize the GUI macro with this workspace's persistent document path."""
    template = GUI_BRIDGE_TEMPLATE_PATH.read_text(encoding="utf-8")
    macro_source = template.replace("__BRIDGE_PORT__", str(GUI_BRIDGE_PORT)).replace(
        "__MODEL_PATH__", json.dumps(str(PROJECT_DOCUMENT_PATH))
    )
    GUI_MACROS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PROJECT_DOCUMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GUI_BRIDGE_MACRO_PATH.write_text(macro_source, encoding="utf-8")


def _start_gui_session() -> Optional[str]:
    """Start the one persistent FreeCAD window if its GUI bridge is not running."""
    if _gui_bridge_is_ready():
        return None

    try:
        freecad_gui = find_freecad_gui()
        if freecad_gui is None:
            return "FreeCAD GUI could not be located for the persistent model session."

        _write_gui_bridge_macro()
        kwargs: Dict[str, Any] = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | 0x01000000  # CREATE_BREAKAWAY_FROM_JOB
            )
        else:
            kwargs["start_new_session"] = True

        subprocess.Popen(
            [freecad_gui, str(GUI_BRIDGE_MACRO_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            shell=False,
            **kwargs,
        )

        deadline = time.monotonic() + GUI_START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if _gui_bridge_is_ready():
                return None
            time.sleep(0.1)

        return (
            "FreeCAD GUI started, but its persistent execution bridge was not ready "
            "within {} seconds.".format(GUI_START_TIMEOUT_SECONDS)
        )
    except OSError:
        return traceback.format_exc()
    except Exception:
        return traceback.format_exc()


def _normalise_gui_result(step_id: int, result: Dict[str, Any]) -> Dict[str, Any]:
    """Accept only the documented execution result produced by the GUI bridge."""
    stdout = result.get("stdout")
    if not isinstance(stdout, str):
        return failed_result(step_id, "", "FreeCAD GUI bridge returned invalid stdout.")

    status = result.get("status")
    if status == "SUCCESS":
        return {
            "step_id": step_id,
            "status": "SUCCESS",
            "stdout": stdout,
            "error_trace": None,
        }
    if status == "FAILED":
        error_trace = result.get("error_trace")
        return failed_result(
            step_id,
            stdout,
            error_trace
            if isinstance(error_trace, str) and error_trace
            else "FreeCAD GUI script execution failed without an error trace.",
        )
    return failed_result(step_id, stdout, "FreeCAD GUI bridge returned an invalid status.")


def execute_in_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run code in the persistent FreeCAD GUI document and update its 3D view.

    The first request starts FreeCAD with a local-only bridge. Every later request
    is sent to that same GUI process, preserving the active document and its
    previous objects. The bridge saves the active document after each success.
    """
    step_id = payload["step_id"]
    code = payload["code"]

    try:
        compile(code, "<sketch2cad-generated-code>", "exec")
    except (SyntaxError, ValueError, TypeError):
        return failed_result(step_id, "", traceback.format_exc())

    try:
        with EXECUTION_LOCK:
            startup_error = _start_gui_session()
            if startup_error is not None:
                return failed_result(step_id, "", startup_error)

            result = _send_gui_bridge_request(
                {"step_id": step_id, "code": code},
                timeout=EXECUTION_TIMEOUT_SECONDS + 5,
            )
            return _normalise_gui_result(step_id, result)
    except socket.timeout:
        return failed_result(
            step_id,
            "",
            "FreeCAD GUI did not respond within {} seconds.".format(
                EXECUTION_TIMEOUT_SECONDS + 5
            ),
        )
    except OSError:
        return failed_result(step_id, "", traceback.format_exc())
    except Exception:
        return failed_result(step_id, "", traceback.format_exc())


def write_output(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Write the local command-line result contract as JSON."""
    if output_path is None:
        output_path = OUTPUT_PATH
    output_path.write_text(
        json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    """Run the compatibility command-line contract and display its model."""
    write_output(execute_in_session(load_input()))


if __name__ == "__main__":
    main()
