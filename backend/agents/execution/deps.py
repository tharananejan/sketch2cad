"""Dependency discovery for the deterministic FreeCAD execution agent."""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional


FREECAD_CLI_CANDIDATES = ("freecadcmd", "freecad")
FREECAD_GUI_CANDIDATES = ("freecad",)
WINDOWS_STANDARD_FREECAD_PATHS = (
    r"C:\Program Files\FreeCAD 1.1\bin\FreeCADCmd.exe",
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe",
    r"C:\Program Files\FreeCAD\bin\FreeCADCmd.exe",
)
MACOS_STANDARD_FREECAD_PATHS = (
    "/Applications/FreeCAD.app/Contents/Resources/bin/FreeCADCmd",
)
LINUX_STANDARD_FREECAD_PATHS = ("/usr/bin/freecadcmd", "/usr/bin/freecad")
WINDOWS_STANDARD_FREECAD_GUI_PATHS = (
    r"C:\Program Files\FreeCAD 1.1\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD\bin\FreeCAD.exe",
)
MACOS_STANDARD_FREECAD_GUI_PATHS = (
    "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
)
LINUX_STANDARD_FREECAD_GUI_PATHS = ("/usr/bin/freecad",)


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


def find_freecad_gui() -> Optional[str]:
    """Return the first configured, PATH-resolved, or standard FreeCAD GUI path."""
    configured_path = os.environ.get("FREECAD_GUI_PATH")
    if configured_path and _is_valid_cli_path(configured_path):
        return configured_path

    for executable in FREECAD_GUI_CANDIDATES:
        resolved_path = shutil.which(executable)
        if resolved_path is not None:
            return resolved_path

    freecad_cli = find_freecad_cli()
    if freecad_cli is not None:
        cli_directory = Path(freecad_cli).parent
        for executable in ("FreeCAD.exe", "freecad.exe", "FreeCAD", "freecad"):
            sibling_path = str(cli_directory / executable)
            if _is_valid_cli_path(sibling_path):
                return sibling_path

    for standard_path in standard_freecad_gui_paths():
        if _is_valid_cli_path(standard_path):
            return standard_path

    return None
