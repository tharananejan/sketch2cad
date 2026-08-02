"""
FreeGen Desktop Launcher
Launches the Sketch2CAD backend API and opens a native desktop window
using PyWebView (non-frameless mode for Windows stability).
"""
import sys
import subprocess
import time
import urllib.request
import atexit
import ctypes
from pathlib import Path

import webview

backend_dir = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Backend process management
# ---------------------------------------------------------------------------
api_process = None

def cleanup():
    global api_process
    if api_process and api_process.poll() is None:
        print("[*] Terminating backend API process tree...")
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(api_process.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            api_process.terminate()

atexit.register(cleanup)

def start_backend_process():
    global api_process
    print("[*] Launching backend API server...")
    api_script = backend_dir / "api_run.py"

    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

    api_process = subprocess.Popen(
        [sys.executable, str(api_script)],
        cwd=str(backend_dir),
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

# ---------------------------------------------------------------------------
# URL detection
# ---------------------------------------------------------------------------
def get_target_url():
    # Check for running Vite dev server first
    for host in ("localhost", "127.0.0.1"):
        try:
            req = urllib.request.Request(
                f"http://{host}:5173",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    print(f"[*] Vite dev server detected at http://{host}:5173")
                    return f"http://{host}:5173"
        except Exception:
            pass

    # Wait for FastAPI production server
    print("[*] Waiting for backend at http://127.0.0.1:8080 ...")
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/", timeout=1) as resp:
                if resp.status == 200:
                    print("[*] Backend ready at http://127.0.0.1:8080")
                    return "http://127.0.0.1:8080"
        except Exception:
            time.sleep(0.5)

    return "http://127.0.0.1:8080"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Launch backend in a completely separate process
    start_backend_process()

    # 2. Resolve the URL to load
    target_url = get_target_url()

    # 3. Calculate window dimensions (2/3 of screen height, right-aligned)
    try:
        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
    except Exception:
        screen_w, screen_h = 1920, 1080

    win_w = 440
    win_h = int(screen_h * 0.70)
    win_x = max(0, screen_w - win_w - 15)
    win_y = int(screen_h * 0.15)

    # 4. Resolve the icon path (freegen.ico next to this script)
    icon_path = str(backend_dir / "freegen.ico")

    # 5. Create a NORMAL (non-frameless) window — frameless is unstable on
    #    Windows with the pythonnet/WinForms backend and causes "not responding"
    window = webview.create_window(
        title="FreeGen",
        url=target_url,
        width=win_w,
        height=win_h,
        x=win_x,
        y=win_y,
        resizable=True,
        on_top=True,
        background_color="#1e1e1e",
    )

    # 6. Set custom window icon using Win32 API (replaces default Python icon)
    def set_window_icon():
        """Set custom icon on the native window handle after it is created."""
        import time as _time
        try:
            user32 = ctypes.windll.user32

            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1

            # Load icon from .ico file
            hicon = user32.LoadImageW(
                0, icon_path, 1,  # IMAGE_ICON
                0, 0,
                0x0010 | 0x0040  # LR_LOADFROMFILE | LR_DEFAULTSIZE
            )

            if not hicon:
                print("[!] Failed to load icon file")
                return

            # Find the window by its title — may take a moment to appear
            hwnd = 0
            for _ in range(20):
                hwnd = user32.FindWindowW(None, "FreeGen")
                if hwnd:
                    break
                _time.sleep(0.25)

            if hwnd:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                print("[*] Custom window icon applied")
            else:
                print("[!] Could not find FreeGen window handle")
        except Exception as e:
            print(f"[!] Could not set window icon: {e}")

    print(f"[*] Opening FreeGen window -> {target_url}")

    try:
        webview.start(debug=False, func=set_window_icon)
    finally:
        cleanup()
