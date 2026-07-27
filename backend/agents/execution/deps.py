"""Dependency discovery for the deterministic FreeCAD execution agent."""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional


FREECAD_CLI_CANDIDATES = ("freecadcmd", "freecad")
WINDOWS_STANDARD_FREECAD_PATHS = (
    r"C:\Program Files\FreeCAD 1.1\bin\FreeCADCmd.exe",
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe",
    r"C:\Program Files\FreeCAD\bin\FreeCADCmd.exe",
)
MACOS_STANDARD_FREECAD_PATHS = (
    "/Applications/FreeCAD.app/Contents/Resources/bin/FreeCADCmd",
)
LINUX_STANDARD_FREECAD_PATHS = ("/usr/bin/freecadcmd", "/usr/bin/freecad")


def _is_valid_cli_path(candidate: str) -> bool:
    """Return whether a candidate points to an existing FreeCAD executable file."""
    try:
        return Path(candidate).expanduser().is_file()
    except (OSError, ValueError):
        return False


def standard_freecad_cli_paths() -> tuple:
    """Return the known FreeCAD executable locations for the current OS."""
    operating_system = platform.system()
    if operating_system == "Windows":
        return WINDOWS_STANDARD_FREECAD_PATHS
    if operating_system == "Darwin":
        return MACOS_STANDARD_FREECAD_PATHS
    if operating_system == "Linux":
        return LINUX_STANDARD_FREECAD_PATHS
    return ()


def find_freecad_cli() -> Optional[str]:
    """Return the first configured, PATH-resolved, or standard FreeCAD CLI path."""
    configured_path = os.environ.get("FREECAD_PATH")
    if configured_path and _is_valid_cli_path(configured_path):
        return configured_path

    for executable in FREECAD_CLI_CANDIDATES:
        resolved_path = shutil.which(executable)
        if resolved_path is not None:
            return resolved_path

    for standard_path in standard_freecad_cli_paths():
        if _is_valid_cli_path(standard_path):
            return standard_path

    return None
