"""Locate the FreeCAD GUI used by the persistent execution session."""

import os
import platform
import shutil
import glob
import re
from pathlib import Path
from typing import Optional, List


WINDOWS_STANDARD_FREECAD_GUI_PATHS = (
    r"C:\Program Files\FreeCAD 1.1\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD 0.21\bin\FreeCAD.exe",
    r"C:\Program Files\FreeCAD 0.20\bin\FreeCAD.exe",
    r"C:\Program Files (x86)\FreeCAD 1.1\bin\FreeCAD.exe",
    r"C:\Program Files (x86)\FreeCAD 1.0\bin\FreeCAD.exe",
    r"C:\Program Files (x86)\FreeCAD\bin\FreeCAD.exe",
    r"C:\Program Files (x86)\FreeCAD 0.21\bin\FreeCAD.exe",
    r"C:\Program Files (x86)\FreeCAD 0.20\bin\FreeCAD.exe",
)
MACOS_STANDARD_FREECAD_GUI_PATHS = (
    "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
)
LINUX_STANDARD_FREECAD_GUI_PATHS = ("/usr/bin/freecad", "/usr/local/bin/freecad")


def _is_valid_path(candidate: str) -> bool:
    """Return whether a candidate points to an existing executable file."""
    try:
        return Path(candidate).expanduser().is_file()
    except (OSError, ValueError):
        return False


def _extract_version_tuple(path_str: str) -> tuple:
    """Extract numeric version numbers from path for sorting (e.g. '1.1' -> (1, 1))."""
    matches = re.findall(r'(\d+)\.(\d+)', path_str)
    if matches:
        return tuple(int(x) for x in matches[-1])
    return (0, 0)


def _find_freecad_in_windows_registry() -> List[str]:
    """Search Windows registry uninstall keys for FreeCAD installations."""
    found = []
    if platform.system() != "Windows":
        return found

    try:
        import winreg
    except ImportError:
        return found

    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\FreeCAD"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\FreeCAD"),
    ]

    for root_key, sub_key in reg_paths:
        try:
            with winreg.OpenKey(root_key, sub_key) as key:
                num_subkeys, _, _ = winreg.QueryInfoKey(key)
                for i in range(num_subkeys):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as item_key:
                            # Check DisplayName or key name
                            display_name = ""
                            try:
                                display_name, _ = winreg.QueryValueEx(item_key, "DisplayName")
                            except OSError:
                                pass

                            if "freecad" in display_name.lower() or "freecad" in subkey_name.lower():
                                # Check InstallLocation
                                try:
                                    install_loc, _ = winreg.QueryValueEx(item_key, "InstallLocation")
                                    if install_loc:
                                        for cand in [
                                            Path(install_loc) / "bin" / "FreeCAD.exe",
                                            Path(install_loc) / "FreeCAD.exe",
                                        ]:
                                            if cand.is_file():
                                                found.append(str(cand))
                                except OSError:
                                    pass

                                # Check DisplayIcon
                                try:
                                    display_icon, _ = winreg.QueryValueEx(item_key, "DisplayIcon")
                                    if display_icon and display_icon.lower().endswith(".exe"):
                                        icon_path = Path(display_icon.strip('"'))
                                        if icon_path.is_file():
                                            found.append(str(icon_path))
                                except OSError:
                                    pass
                    except OSError:
                        continue
        except OSError:
            continue

    return found


def _scan_windows_drives() -> List[str]:
    """Dynamically scan standard folders across Windows drives."""
    candidates = []
    drives = ["C:", "D:", "E:"]
    
    # Check LocalAppData & AppData
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        for p in glob.glob(os.path.join(local_appdata, "Programs", "FreeCAD*", "bin", "FreeCAD.exe")):
            candidates.append(p)
        for p in glob.glob(os.path.join(local_appdata, "Programs", "FreeCAD*", "FreeCAD.exe")):
            candidates.append(p)

    appdata = os.environ.get("APPDATA", "")
    if appdata:
        for p in glob.glob(os.path.join(appdata, "FreeCAD*", "bin", "FreeCAD.exe")):
            candidates.append(p)

    for drive in drives:
        patterns = [
            f"{drive}\\Program Files\\FreeCAD*\\bin\\FreeCAD.exe",
            f"{drive}\\Program Files (x86)\\FreeCAD*\\bin\\FreeCAD.exe",
            f"{drive}\\FreeCAD*\\bin\\FreeCAD.exe",
            f"{drive}\\FreeCAD*\\FreeCAD.exe",
        ]
        for pat in patterns:
            for match in glob.glob(pat):
                if _is_valid_path(match):
                    candidates.append(match)

    return candidates


def standard_freecad_gui_paths() -> List[str]:
    """Return the known and discovered FreeCAD GUI executable locations for the current OS."""
    operating_system = platform.system()
    discovered = []

    if operating_system == "Windows":
        discovered.extend(_scan_windows_drives())
        discovered.extend(_find_freecad_in_windows_registry())
        discovered.extend(WINDOWS_STANDARD_FREECAD_GUI_PATHS)
    elif operating_system == "Darwin":
        discovered.extend(MACOS_STANDARD_FREECAD_GUI_PATHS)
        for pat in ["/Applications/FreeCAD*.app/Contents/MacOS/FreeCAD", "~/Applications/FreeCAD*.app/Contents/MacOS/FreeCAD"]:
            discovered.extend(glob.glob(os.path.expanduser(pat)))
    elif operating_system == "Linux":
        discovered.extend(LINUX_STANDARD_FREECAD_GUI_PATHS)
        for pat in ["/usr/bin/freecad*", "/usr/local/bin/freecad*", "/opt/freecad*/bin/freecad", "~/.local/bin/freecad*"]:
            discovered.extend(glob.glob(os.path.expanduser(pat)))

    # Deduplicate preserving order
    unique_candidates = []
    seen = set()
    for path in discovered:
        normalized = os.path.normpath(path).lower() if operating_system == "Windows" else os.path.normpath(path)
        if normalized not in seen and _is_valid_path(path):
            seen.add(normalized)
            unique_candidates.append(path)

    # Sort candidates by version descending so highest version (1.1, 1.0, 0.21...) is prioritized
    unique_candidates.sort(key=lambda p: _extract_version_tuple(p), reverse=True)
    return unique_candidates


def find_freecad_gui() -> Optional[str]:
    """Return the first configured, PATH-resolved, or dynamically discovered FreeCAD GUI path."""
    configured_path = os.environ.get("FREECAD_GUI_PATH")
    if configured_path and _is_valid_path(configured_path):
        return configured_path

    # Check PATH
    for name in ("freecad", "FreeCAD", "freecad.exe", "FreeCAD.exe"):
        resolved_path = shutil.which(name)
        if resolved_path is not None and _is_valid_path(resolved_path):
            return resolved_path

    # Check dynamically discovered & standard paths
    candidates = standard_freecad_gui_paths()
    if candidates:
        return candidates[0]

    return None

