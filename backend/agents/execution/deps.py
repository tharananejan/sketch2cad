"""Locate the FreeCAD GUI used by the persistent execution session."""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional


WINDOWS_STANDARD_FREECAD_GUI_PATHS = (
    r"C:\Program Files\FreeCAD 1.1\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD\bin\FreeCAD.exe",
)
MACOS_STANDARD_FREECAD_GUI_PATHS = (
    "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
)
LINUX_STANDARD_FREECAD_GUI_PATHS = ("/usr/bin/freecad",)


def _is_valid_path(candidate: str) -> bool:
    """Return whether a candidate points to an existing executable file."""
    try:
        return Path(candidate).expanduser().is_file()
    except (OSError, ValueError):
        return False


def standard_freecad_gui_paths() -> tuple:
    """Return the known FreeCAD GUI executable locations for the current OS."""
    operating_system = platform.system()
    if operating_system == "Windows":
        return WINDOWS_STANDARD_FREECAD_GUI_PATHS
    if operating_system == "Darwin":
        return MACOS_STANDARD_FREECAD_GUI_PATHS
    if operating_system == "Linux":
        return LINUX_STANDARD_FREECAD_GUI_PATHS
    return ()


def find_freecad_gui() -> Optional[str]:
    """Return the first configured, PATH-resolved, or standard FreeCAD GUI path."""
    configured_path = os.environ.get("FREECAD_GUI_PATH")
    if configured_path and _is_valid_path(configured_path):
        return configured_path

    resolved_path = shutil.which("freecad")
    if resolved_path is not None:
        return resolved_path

    for standard_path in standard_freecad_gui_paths():
        if _is_valid_path(standard_path):
            return standard_path

    return None
