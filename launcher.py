import os
import sys
import subprocess
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# In PyInstaller --onefile mode, sys.executable points to the actual .exe location,
# whereas __file__ points to the temporary _MEIPASS extraction folder.
if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
else:
    ROOT_DIR = Path(__file__).resolve().parent

BACKEND_DIR = ROOT_DIR / "backend"
VENV_DIR = BACKEND_DIR / ".venv"
PYTHON_EXE = VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"
LOG_FILE = ROOT_DIR / "freegen_setup_error.log"

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "websockets",
    "httpx",
    "requests",
    "pydantic",
    "openai",
    "groq",
    "python-dotenv",
]

def find_system_python():
    """Find a usable system Python interpreter on Windows/macOS/Linux."""
    candidates = []
    
    # If running directly from python (unfrozen), use current sys.executable
    if not getattr(sys, "frozen", False):
        candidates.append(sys.executable)

    # Check "python" in PATH
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        res = subprocess.run(["python", "-c", "import sys; print(sys.executable)"],
                             capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0 and res.stdout.strip():
            candidates.append(res.stdout.strip())
    except Exception:
        pass

    # Check "py" launcher (Windows standard)
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        res = subprocess.run(["py", "-3", "-c", "import sys; print(sys.executable)"],
                             capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0 and res.stdout.strip():
            candidates.append(res.stdout.strip())
    except Exception:
        pass

    # Check common Windows install directories in %LOCALAPPDATA%
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            programs_dir = Path(local_appdata) / "Programs" / "Python"
            if programs_dir.exists():
                for py_dir in programs_dir.glob("Python3*"):
                    p = py_dir / "python.exe"
                    if p.exists():
                        candidates.append(str(p))

    for cand in candidates:
        cand_path = Path(cand)
        if cand_path.exists() and "FreeGen.exe" not in cand_path.name:
            return str(cand_path)

    return None


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FreeGen Setup")
        self.geometry("440x160")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        # Center window on screen
        self.eval("tk::PlaceWindow . center")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e1e", foreground="#e0e0e0", font=("Segoe UI", 10))
        style.configure("TProgressbar", thickness=16, troughcolor="#2d2d2d", background="#007acc")

        self.title_label = ttk.Label(self, text="FreeGen V2.0", font=("Segoe UI", 12, "bold"), foreground="#00aaff")
        self.title_label.pack(pady=(15, 5))

        self.status_label = ttk.Label(self, text="Initializing...")
        self.status_label.pack(pady=(0, 10))

        self.progress = ttk.Progressbar(self, orient="horizontal", length=360, mode="indeterminate")
        self.progress.pack(pady=5)
        self.progress.start(10)

        # Set icon if it exists
        icon_path = BACKEND_DIR / "freegen.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Start setup thread
        threading.Thread(target=self.run_setup, daemon=True).start()

    def update_status(self, text):
        self.status_label.config(text=text)

    def show_error_and_exit(self, title, message):
        self.withdraw()
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\nMessage:\n{message}\n")
        except Exception:
            pass
        messagebox.showerror(title, message)
        self.destroy()
        sys.exit(1)

    def run_setup(self):
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            # 1. Check for system Python
            self.update_status("Checking for Python interpreter...")
            system_python = find_system_python()
            if not system_python:
                self.after(0, self.show_error_and_exit, "Python Not Found",
                           "Python 3.10+ is required to run FreeGen.\n\n"
                           "Please install Python from https://www.python.org/downloads/ "
                           "and make sure to check 'Add Python to PATH' during installation.")
                return

            # 2. Setup Virtual Environment if not present or incomplete
            needs_install = False
            if not VENV_DIR.exists() or not PYTHON_EXE.exists():
                self.update_status("Creating virtual environment (First time)...")
                res = subprocess.run([system_python, "-m", "venv", str(VENV_DIR)],
                                     capture_output=True, text=True, creationflags=flags)
                if res.returncode != 0:
                    err = res.stderr.strip() or res.stdout.strip()
                    raise RuntimeError(f"Failed to create virtual environment:\n{err}")
                needs_install = True
            else:
                verify_cmd = [str(PYTHON_EXE), "-c", "import fastapi, uvicorn, websockets, groq, dotenv"]
                res = subprocess.run(verify_cmd, capture_output=True, text=True, creationflags=flags)
                if res.returncode != 0:
                    needs_install = True

            if needs_install:
                self.update_status("Installing dependencies (May take 1-2 minutes)...")
                pip_cmd = [str(PYTHON_EXE), "-m", "pip", "install"] + REQUIRED_PACKAGES
                res = subprocess.run(pip_cmd, capture_output=True, text=True, creationflags=flags)
                if res.returncode != 0:
                    err = res.stderr.strip() or res.stdout.strip()
                    raise RuntimeError(f"Failed to install dependencies:\n{err}")

            # 3. Check for FreeCAD installation
            self.update_status("Detecting FreeCAD installation...")
            freecad_check_code = (
                "import sys; "
                "sys.path.insert(0, r'" + str((BACKEND_DIR / "agents" / "execution").resolve()) + "'); "
                "from deps import find_freecad_gui; "
                "fc = find_freecad_gui(); "
                "print(fc if fc else 'NOT_FOUND')"
            )
            res = subprocess.run([str(PYTHON_EXE), "-c", freecad_check_code],
                                 capture_output=True, text=True, creationflags=flags)
            fc_path = res.stdout.strip() if res.returncode == 0 else "NOT_FOUND"

            if not fc_path or fc_path == "NOT_FOUND":
                self.after(0, messagebox.showwarning, "FreeCAD Not Detected",
                           "FreeCAD was not automatically found on your computer.\n\n"
                           "To generate and view 3D CAD models, please install FreeCAD from:\n"
                           "https://www.freecad.org/downloads.php\n\n"
                           "FreeGen will still launch, and you can also set FREECAD_GUI_PATH in your .env file.")

            # 4. Launch Desktop App
            self.update_status("Launching FreeGen...")
            desktop_run_path = BACKEND_DIR / "desktop_run.py"
            if not desktop_run_path.exists():
                raise FileNotFoundError(f"Cannot find desktop runner at: {desktop_run_path}")

            spawn_flags = 0
            if sys.platform == "win32":
                spawn_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

            proc = subprocess.Popen(
                [str(PYTHON_EXE), str(desktop_run_path)],
                cwd=str(BACKEND_DIR),
                creationflags=spawn_flags
            )

            # Hide launcher setup window
            self.after(100, self.withdraw)

            # Keep launcher alive until desktop app is closed by the user
            proc.wait()

            # Cleanly exit launcher
            self.after(0, self.destroy)
            sys.exit(0)

        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"{str(e)}\n\nDetails:\n{tb}\n\nLogged to: {LOG_FILE}"
            self.after(0, self.show_error_and_exit, "Setup Error", error_msg)


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()


