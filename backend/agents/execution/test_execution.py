"""Unit tests for the deterministic FreeCAD execution bridge."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


EXECUTION_DIR = Path(__file__).resolve().parent
if str(EXECUTION_DIR) not in sys.path:
    sys.path.insert(0, str(EXECUTION_DIR))


def load_router():
    """Load the importable execution core from its file path."""
    spec = importlib.util.spec_from_file_location(
        "execution_router_under_test", EXECUTION_DIR / "execution_router.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load execution_router.py for testing.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExecutionRouterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temporary_directory.name)
        self.router = load_router()
        self.router.INPUT_PATH = self.temp_path / "input.json"
        self.router.OUTPUT_PATH = self.temp_path / "output.json"
        self.router.TEMP_SCRIPT_PATH = self.temp_path / "temp_script.py"
        self.payload = {"step_id": 42, "code": "print('hello from FreeCAD')\n"}
        self.router.INPUT_PATH.write_text(json.dumps(self.payload), encoding="utf-8")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def read_output(self):
        return json.loads(self.router.OUTPUT_PATH.read_text(encoding="utf-8"))

    def run_headless_contract(self):
        self.router.write_output(self.router.execute(self.router.load_input()))

    def test_success_preserves_stdout_and_removes_temp_script(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Created cube\r\n", stderr=b""
        )

        with patch.object(
            self.router, "find_freecad_cli", return_value="C:/FreeCAD/freecadcmd.exe"
        ), patch.object(self.router.subprocess, "run", return_value=completed) as run:
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "SUCCESS",
                "stdout": "Created cube\r\n",
                "error_trace": None,
            },
        )
        run.assert_called_once_with(
            ["C:/FreeCAD/freecadcmd.exe", "-c", str(self.router.TEMP_SCRIPT_PATH)],
            capture_output=True,
            check=False,
            shell=False,
            timeout=60,
        )
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())

    def test_success_discards_nonfailure_stderr(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Done\n", stderr=b"Warning\r\n"
        )

        with patch.object(self.router, "find_freecad_cli", return_value="freecadcmd"), patch.object(
            self.router.subprocess, "run", return_value=completed
        ):
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "SUCCESS",
                "stdout": "Done\n",
                "error_trace": None,
            },
        )
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())

    def test_success_removes_freecad_progress_noise(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(
                b"Created mesh\n"
                b"saving......\n\t(0 %)\t\r\t(50 %)\t\r\t(100 %)\t\r"
                b"Export complete\n"
            ),
            stderr=b"",
        )

        with patch.object(self.router, "find_freecad_cli", return_value="freecadcmd"), patch.object(
            self.router.subprocess, "run", return_value=completed
        ):
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "SUCCESS",
                "stdout": "Created mesh\nExport complete\n",
                "error_trace": None,
            },
        )
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())

    def test_start_gui_session_launches_one_persistent_bridge(self):
        self.router.GUI_MACROS_DIRECTORY = self.temp_path / "macros"
        self.router.GUI_BRIDGE_MACRO_PATH = (
            self.router.GUI_MACROS_DIRECTORY / "sketch2cad_session.FCMacro"
        )
        self.router.PROJECT_DOCUMENT_PATH = self.temp_path / "models" / "sketch2cad.FCStd"

        with patch.object(
            self.router, "_gui_bridge_is_ready", side_effect=[False, True]
        ), patch.object(
            self.router, "find_freecad_gui", return_value="C:/FreeCAD/FreeCAD.exe"
        ), patch.object(self.router.subprocess, "Popen") as popen:
            self.assertIsNone(self.router._start_gui_session())

        macro_source = self.router.GUI_BRIDGE_MACRO_PATH.read_text(encoding="utf-8")
        self.assertIn(str(self.router.GUI_BRIDGE_PORT), macro_source)
        self.assertIn(json.dumps(str(self.router.PROJECT_DOCUMENT_PATH)), macro_source)
        popen.assert_called_once_with(
            ["C:/FreeCAD/FreeCAD.exe", str(self.router.GUI_BRIDGE_MACRO_PATH)],
            stdout=self.router.subprocess.DEVNULL,
            stderr=self.router.subprocess.DEVNULL,
            shell=False,
        )

    def test_successful_request_uses_existing_freecad_gui_session(self):
        code = "print('generated code')\n"
        payload = {"step_id": 42, "code": code}
        gui_result = {
            "step_id": 42,
            "status": "SUCCESS",
            "stdout": "Created bottle\n",
            "error_trace": None,
        }

        with patch.object(self.router, "_start_gui_session", return_value=None), patch.object(
            self.router, "_send_gui_bridge_request", return_value=gui_result
        ) as send:
            result = self.router.execute_and_display(payload)

        send.assert_called_once_with(
            {"step_id": 42, "code": code},
            timeout=self.router.EXECUTION_TIMEOUT_SECONDS + 5,
        )
        self.assertEqual(
            result,
            {
                "step_id": 42,
                "status": "SUCCESS",
                "stdout": "Created bottle\n",
                "error_trace": None,
            },
        )

    def test_syntax_failure_does_not_start_or_contact_freecad_gui(self):
        payload = {"step_id": 42, "code": "def missing_colon()\n"}

        with patch.object(self.router, "_start_gui_session") as start, patch.object(
            self.router, "_send_gui_bridge_request"
        ) as send:
            result = self.router.execute_and_display(payload)

        self.assertEqual(result["status"], "FAILED")
        self.assertIn("SyntaxError", result["error_trace"])
        start.assert_not_called()
        send.assert_not_called()

    def test_zero_exit_script_exception_is_reported_as_failure(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"Exported STEP file\r\n",
            stderr=(
                b"Exception while processing file: temp_script.py "
                b"[None of the objects can be exported to a mesh file]\r\n"
            ),
        )

        with patch.object(self.router, "find_freecad_cli", return_value="freecadcmd"), patch.object(
            self.router.subprocess, "run", return_value=completed
        ):
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "FAILED",
                "stdout": "Exported STEP file\r\n",
                "error_trace": (
                    "Exception while processing file: temp_script.py "
                    "[None of the objects can be exported to a mesh file]\r\n"
                ),
            },
        )
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())

    def test_nonzero_exit_preserves_partial_stdout_and_trace(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=b"Started operation\r\n",
            stderr=b"Traceback (most recent call last):\r\nRuntimeError: bad shape\r\n",
        )

        with patch.object(self.router, "find_freecad_cli", return_value="freecadcmd"), patch.object(
            self.router.subprocess, "run", return_value=completed
        ):
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "FAILED",
                "stdout": "Started operation\r\n",
                "error_trace": "Traceback (most recent call last):\r\nRuntimeError: bad shape\r\n",
            },
        )
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())

    def test_missing_cli_returns_failure_without_running_subprocess(self):
        with patch.object(self.router, "find_freecad_cli", return_value=None), patch.object(
            self.router.subprocess, "run"
        ) as run:
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "FAILED",
                "stdout": "",
                "error_trace": "FreeCAD CLI could not be located via FREECAD_PATH, PATH, or standard installation paths.",
            },
        )
        run.assert_not_called()
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())

    def test_timeout_retains_partial_output_and_removes_temp_script(self):
        timeout_error = subprocess.TimeoutExpired(
            ["freecadcmd", "temp_script.py"],
            60,
            output=b"Started operation\r\n",
            stderr=b"",
        )

        with patch.object(self.router, "find_freecad_cli", return_value="freecadcmd"), patch.object(
            self.router.subprocess, "run", side_effect=timeout_error
        ):
            self.run_headless_contract()

        self.assertEqual(
            self.read_output(),
            {
                "step_id": 42,
                "status": "FAILED",
                "stdout": "Started operation\r\n",
                "error_trace": "Execution timed out after 60 seconds.",
            },
        )
        self.assertFalse(self.router.TEMP_SCRIPT_PATH.exists())


class DependencyTests(unittest.TestCase):
    def test_find_freecad_cli_uses_valid_environment_path_first(self):
        import deps

        configured_path = r"C:\Custom\FreeCADCmd.exe"
        with patch.dict(deps.os.environ, {"FREECAD_PATH": configured_path}, clear=True), patch.object(
            deps, "_is_valid_cli_path", return_value=True
        ) as is_valid, patch.object(deps.shutil, "which") as which:
            self.assertEqual(deps.find_freecad_cli(), configured_path)

        is_valid.assert_called_once_with(configured_path)
        which.assert_not_called()

    def test_find_freecad_cli_checks_supported_commands_in_order(self):
        import deps

        with patch.dict(deps.os.environ, {}, clear=True), patch.object(
            deps, "_is_valid_cli_path", return_value=False
        ), patch.object(deps.shutil, "which", side_effect=[None, "/usr/bin/freecad"]):
            self.assertEqual(deps.find_freecad_cli(), "/usr/bin/freecad")

    def test_find_freecad_cli_uses_windows_standard_path_as_fallback(self):
        import deps

        expected_path = deps.WINDOWS_STANDARD_FREECAD_PATHS[0]
        with patch.dict(deps.os.environ, {}, clear=True), patch.object(
            deps.shutil, "which", return_value=None
        ), patch.object(deps.platform, "system", return_value="Windows"), patch.object(
            deps,
            "_is_valid_cli_path",
            side_effect=lambda candidate: candidate == expected_path,
        ):
            self.assertEqual(deps.find_freecad_cli(), expected_path)

    def test_find_freecad_gui_uses_configured_path_first(self):
        import deps

        configured_path = r"C:\Custom\FreeCAD.exe"
        with patch.dict(deps.os.environ, {"FREECAD_GUI_PATH": configured_path}, clear=True), patch.object(
            deps, "_is_valid_cli_path", return_value=True
        ) as is_valid, patch.object(deps.shutil, "which") as which:
            self.assertEqual(deps.find_freecad_gui(), configured_path)

        is_valid.assert_called_once_with(configured_path)
        which.assert_not_called()


if __name__ == "__main__":
    unittest.main()
