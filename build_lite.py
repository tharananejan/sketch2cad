import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BUILDS_DIR = ROOT_DIR / "builds"
APP_DIR = BUILDS_DIR / "FreeGen"
ZIP_PATH = BUILDS_DIR / "FreeGen-Lite.zip"

def build_frontend():
    print("[*] Building frontend...")
    web_dir = ROOT_DIR / "apps" / "web"
    subprocess.run(["npm", "run", "build"], cwd=str(web_dir), shell=True, check=True)

def copy_files():
    print("[*] Copying files...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    
    # Copy backend
    shutil.copytree(
        ROOT_DIR / "backend",
        APP_DIR / "backend",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".venv", "venv", "env")
    )
    
    # Copy frontend dist
    shutil.copytree(
        ROOT_DIR / "apps" / "web" / "dist",
        APP_DIR / "apps" / "web" / "dist"
    )

def create_run_script():
    print("[*] Creating run script...")
    bat_content = """@echo off
echo =========================================
echo Starting FreeGen (Lite)
echo =========================================

REM Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH! Please install Python.
    pause
    exit /b
)

REM Setup virtual environment if it doesn't exist
if not exist "backend\\.venv" (
    echo [*] Setting up first-time environment. This may take a minute...
    python -m venv backend\\.venv
    call backend\\.venv\\Scripts\\activate.bat
    echo [*] Installing dependencies...
    pip install fastapi uvicorn websockets pywebview httpx pydantic openai
) else (
    call backend\\.venv\\Scripts\\activate.bat
)

REM Run the app
echo [*] Launching FreeGen Desktop Interface...
cd backend
python desktop_run.py

pause
"""
    (APP_DIR / "Run_FreeGen.bat").write_text(bat_content)

def create_zip():
    print("[*] Zipping application...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    
    shutil.make_archive(str(ZIP_PATH.with_suffix('')), 'zip', BUILDS_DIR, "FreeGen")
    print(f"[+] Zip created at: {ZIP_PATH}")

def main():
    BUILDS_DIR.mkdir(exist_ok=True)
    build_frontend()
    copy_files()
    create_run_script()
    create_zip()
    print("\n[+] Build complete! The lite app is ready in the 'builds' folder.")

if __name__ == "__main__":
    main()
