"""Unit tests for the persistent FreeCAD execution session."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


EXECUTION_DIR = Path(__file__).resolve().parent
if str(EXECUTION_DIR) not in sys.path:
    sys.path.insert(0, str(EXECUTION_DIR))


def load_router():
    """Load the execution core without starting FastAPI or FreeCAD."""
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

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_load_input_accepts_the_contract(self):
        input_path = self.temp_path / "input.json"
        expected = {"step_id": 42, "code": "print('hello')\n"}
        input_path.write_text(json.dumps(expected), encoding="utf-8")

        self.assertEqual(self.router.load_input(input_path), expected)

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

    def test_successful_request_uses_the_existing_gui_session(self):
        payload = {"step_id": 42, "code": "print('generated code')\n"}
        gui_result = {
            "step_id": 42,
            "status": "SUCCESS",
            "stdout": "Created bottle\n",
            "error_trace": None,
        }

        with patch.object(self.router, "_start_gui_session", return_value=None), patch.object(
            self.router, "_send_gui_bridge_request", return_value=gui_result
        ) as send:
            result = self.router.execute_in_session(payload)

        send.assert_called_once_with(
            payload, timeout=self.router.EXECUTION_TIMEOUT_SECONDS + 5
        )
        self.assertEqual(result, gui_result)

    def test_gui_script_failure_is_returned_to_the_error_handler(self):
        payload = {"step_id": 42, "code": "raise RuntimeError('bad cap')\n"}
        gui_result = {
            "step_id": 42,
            "status": "FAILED",
            "stdout": "",
            "error_trace": "Traceback\nRuntimeError: bad cap\n",
        }

        with patch.object(self.router, "_start_gui_session", return_value=None), patch.object(
            self.router, "_send_gui_bridge_request", return_value=gui_result
        ):
            result = self.router.execute_in_session(payload)

        self.assertEqual(result, gui_result)

    def test_syntax_failure_does_not_start_or_contact_freecad(self):
        payload = {"step_id": 42, "code": "def missing_colon()\n"}

        with patch.object(self.router, "_start_gui_session") as start, patch.object(
            self.router, "_send_gui_bridge_request"
        ) as send:
            result = self.router.execute_in_session(payload)

        self.assertEqual(result["status"], "FAILED")
        self.assertIn("SyntaxError", result["error_trace"])
        start.assert_not_called()
        send.assert_not_called()


class DependencyTests(unittest.TestCase):
    def test_find_freecad_gui_uses_configured_path_first(self):
        import deps

        configured_path = r"C:\Custom\FreeCAD.exe"
        with patch.dict(deps.os.environ, {"FREECAD_GUI_PATH": configured_path}, clear=True), patch.object(
            deps, "_is_valid_path", return_value=True
        ) as is_valid, patch.object(deps.shutil, "which") as which:
            self.assertEqual(deps.find_freecad_gui(), configured_path)

        is_valid.assert_called_once_with(configured_path)
        which.assert_not_called()

    def test_find_freecad_gui_uses_path_before_standard_locations(self):
        import deps

        with patch.dict(deps.os.environ, {}, clear=True), patch.object(
            deps.shutil, "which", return_value="/usr/bin/freecad"
        ) as which:
            self.assertEqual(deps.find_freecad_gui(), "/usr/bin/freecad")

        which.assert_called_once_with("freecad")


if __name__ == "__main__":
    unittest.main()
