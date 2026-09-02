"""
FreeGen Desktop Launcher
Launches the FreeGen backend API and opens the modern UI using native Edge/Chrome
App Mode (or the default browser) without Python GUI wrapper dependencies.
"""
import sys
import subprocess
import time
import urllib.request
import atexit
import ctypes
import os
import shutil
import webbrowser
from pathlib import Path

backend_dir = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Backend process management
# ---------------------------------------------------------------------------
api_process = None

ALL_PORTS = [38080, 38000, 38001, 38002, 38003, 38004]

def kill_ports():
    """Ensure no background API or microservices stay listening on our ports."""
    if sys.platform == "win32":
        for port in ALL_PORTS:
            try:
                output = subprocess.check_output(f'netstat -ano | findstr /R ":{port} "', shell=True).decode()
                for line in output.splitlines():
                    if "LISTENING" in line:
                        parts = line.strip().split()
                        pid = parts[-1]
                        if pid and pid != "0" and pid != str(os.getpid()):
                            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

def cleanup():
    global api_process
    print("[*] Shutting down FreeGen backend and microservices...")
    if api_process and api_process.poll() is None:
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(api_process.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
        else:
            api_process.terminate()
            try:
                api_process.wait(timeout=2)
            except Exception:
                api_process.kill()

    kill_ports()
    print("[+] All backend services stopped.")

atexit.register(cleanup)

def start_backend_process():
    global api_process
    print("[*] Launching FreeGen backend API server...")
    api_script = backend_dir / "api_run.py"

    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

    log_path = backend_dir / "freegen_backend.log"
    try:
        log_file = open(log_path, "w", encoding="utf-8")
    except Exception:
        log_file = subprocess.DEVNULL

    api_process = subprocess.Popen(
        [sys.executable, str(api_script)],
        cwd=str(backend_dir),
        creationflags=flags,
        stdout=log_file,
        stderr=subprocess.STDOUT,
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
    print("[*] Waiting for backend at http://127.0.0.1:38080 ...")
    for _ in range(40):
        if api_process and api_process.poll() is not None:
            print(f"[!] Backend API process exited with code {api_process.returncode}. Check freegen_backend.log for details.")
            break

        try:
            with urllib.request.urlopen("http://127.0.0.1:38080/health", timeout=1) as resp:
                if resp.status == 200:
                    print("[*] Backend ready at http://127.0.0.1:38080")
                    return "http://127.0.0.1:38080"
        except Exception:
            try:
                with urllib.request.urlopen("http://127.0.0.1:38080/", timeout=1) as resp:
                    if resp.status in (200, 404):
                        print("[*] Backend ready at http://127.0.0.1:38080")
                        return "http://127.0.0.1:38080"
            except Exception:
                time.sleep(0.5)

    return "http://127.0.0.1:38080"

# ---------------------------------------------------------------------------
# Browser App Mode Detection
# ---------------------------------------------------------------------------
def find_app_mode_browser():
    """Find Microsoft Edge or Google Chrome for standalone App Mode."""
    if sys.platform == "win32":
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        # Also check local app data
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            candidates.append(os.path.join(local_appdata, "Microsoft", "Edge", "Application", "msedge.exe"))
            candidates.append(os.path.join(local_appdata, "Google", "Chrome", "Application", "chrome.exe"))

        for cand in candidates:
            if Path(cand).is_file():
                return cand

        edge_in_path = shutil.which("msedge") or shutil.which("msedge.exe")
        if edge_in_path:
            return edge_in_path

        chrome_in_path = shutil.which("chrome") or shutil.which("chrome.exe")
        if chrome_in_path:
            return chrome_in_path

    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
        for cand in candidates:
            if Path(cand).is_file():
                return cand

    elif sys.platform.startswith("linux"):
        for name in ("microsoft-edge", "google-chrome", "chromium-browser", "chromium"):
            p = shutil.which(name)
            if p:
                return p

    return None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Launch backend in a completely separate process
    start_backend_process()

    # 2. Resolve the URL to load
    target_url = get_target_url()

    # 3. Calculate window dimensions (approx 70% of screen height, right-aligned)
    try:
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
        else:
            screen_w, screen_h = 1920, 1080
    except Exception:
        screen_w, screen_h = 1920, 1080

    win_w = 460
    win_h = int(screen_h * 0.72)
    win_x = max(0, screen_w - win_w - 20)
    win_y = int(screen_h * 0.14)

    # 4. Launch in Edge/Chrome App mode or default browser
    browser_exe = find_app_mode_browser()
    browser_proc = None

    try:
        if browser_exe:
            print(f"[*] Launching FreeGen App window ({Path(browser_exe).name}) -> {target_url}")
            import tempfile
            profile_dir = Path(tempfile.gettempdir()) / "FreeGen_WebProfile"
            profile_dir.mkdir(parents=True, exist_ok=True)
            app_args = [
                browser_exe,
                f"--app={target_url}",
                f"--user-data-dir={profile_dir}",
                f"--window-size={win_w},{win_h}",
                f"--window-position={win_x},{win_y}",
                "--no-first-run",
                "--no-default-browser-check",
            ]
            browser_proc = subprocess.Popen(app_args)
            # Wait until user closes the app window
            browser_proc.wait()
        else:
            print(f"[*] Opening FreeGen in default web browser -> {target_url}")
            webbrowser.open(target_url)
            # Keep backend alive until interrupted
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Exiting FreeGen...")
    finally:
        cleanup()

