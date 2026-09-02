import os
import shutil
import subprocess
import zipfile
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BUILDS_DIR = ROOT_DIR / "builds"
APP_DIR = BUILDS_DIR / "FreeGen V2.0"
ZIP_PATH = BUILDS_DIR / "FreeGen-V2.0.zip"

def build_frontend():
    print("[*] Building frontend...")
    web_dir = ROOT_DIR / "apps" / "web"
    subprocess.run(["npm", "run", "build"], cwd=str(web_dir), shell=True, check=True)

def copy_files():
    print("[*] Copying files...")
    if APP_DIR.exists():
        try:
            shutil.rmtree(APP_DIR)
        except Exception:
            for item in APP_DIR.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                except Exception:
                    pass
    
    # Copy backend
    shutil.copytree(
        ROOT_DIR / "backend",
        APP_DIR / "backend",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".venv", "venv", "env", "freegen_backend.log")
    )
    
    # Copy frontend dist
    shutil.copytree(
        ROOT_DIR / "apps" / "web" / "dist",
        APP_DIR / "apps" / "web" / "dist",
        dirs_exist_ok=True
    )

    # Embed .env inside root and backend
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        shutil.copy2(env_file, APP_DIR / ".env")
        shutil.copy2(env_file, APP_DIR / "backend" / ".env")

    # Copy launcher script
    shutil.copy2(ROOT_DIR / "launcher.py", APP_DIR / "launcher.py")

def create_scripts():
    print("[*] Creating Smart App Control-safe launchers (Run_FreeGen.bat & FreeGen.vbs)...")
    
    bat_content = """@echo off
title FreeGen
cd /d "%~dp0"
if exist "backend\\.venv\\Scripts\\python.exe" (
    start "" "backend\\.venv\\Scripts\\python.exe" "backend\\desktop_run.py"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        start "" python "launcher.py"
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            start "" py "launcher.py"
        ) else (
            echo Python is not installed or not in PATH! Please install Python 3.10+.
            pause
        )
    )
)
"""
    (APP_DIR / "Run_FreeGen.bat").write_text(bat_content, encoding="utf-8")

    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\n'
        'currentDir = fso.GetParentFolderName(WScript.ScriptFullName)\n'
        'WshShell.CurrentDirectory = currentDir\n\n'
        'If fso.FileExists(currentDir & "\\backend\\.venv\\Scripts\\python.exe") Then\n'
        '    WshShell.Run """" & currentDir & "\\backend\\.venv\\Scripts\\python.exe"" """ & currentDir & "\\backend\\desktop_run.py""", 0, False\n'
        'Else\n'
        '    WshShell.Run "python """ & currentDir & "\\launcher.py""", 0, False\n'
        'End If\n'
    )
    (APP_DIR / "FreeGen.vbs").write_text(vbs_content, encoding="utf-8")

def create_launcher():
    print("[*] Creating FreeGen.exe launcher...")
    
    # Ensure pyinstaller is installed
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    icon_path = ROOT_DIR / "backend" / "freegen.ico"
    launcher_script = ROOT_DIR / "launcher.py"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--icon={icon_path}",
        "--distpath", str(APP_DIR),
        "--name", "FreeGen",
        str(launcher_script)
    ]
    subprocess.run(cmd, check=True)
    
    # Clean up pyinstaller build artifacts
    build_dir = ROOT_DIR / "build"
    spec_file = ROOT_DIR / "FreeGen.spec"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()

def create_installer():
    print("[*] Creating FreeGen-Setup.exe single-file installer...")
    import tempfile
    installer_exe = BUILDS_DIR / "FreeGen-Setup.exe"
    
    # 1. Create a flat zip of the application bundle
    temp_dir = Path(tempfile.mkdtemp(prefix="freegen_build_"))
    app_zip = temp_dir / "freegen_app.zip"
    with zipfile.ZipFile(app_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(APP_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, APP_DIR)
                z.write(full_path, rel_path)

    # 2. Create the setup script that runs when the user runs the installer
    setup_bat = temp_dir / "setup.bat"
    setup_bat_content = """@echo off
title FreeGen Setup
cd /d "%~dp0"

echo ======================================================
echo             Installing FreeGen V2.0...
echo ======================================================

set "INSTALL_DIR=%LOCALAPPDATA%\\Programs\\FreeGen"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [*] Extracting application files...
powershell -ExecutionPolicy Bypass -NoProfile -Command "$dest = Join-Path $env:LOCALAPPDATA 'Programs\\FreeGen'; if (Test-Path (Join-Path $dest 'FreeGen V2.0')) { Remove-Item -Recurse -Force (Join-Path $dest 'FreeGen V2.0') }; Expand-Archive -LiteralPath '%~dp0freegen_app.zip' -DestinationPath $dest -Force"

echo [*] Creating Desktop and Start Menu shortcuts...
powershell -ExecutionPolicy Bypass -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $target = Join-Path $env:LOCALAPPDATA 'Programs\\FreeGen\\FreeGen.vbs'; $workDir = Join-Path $env:LOCALAPPDATA 'Programs\\FreeGen'; $ico = Join-Path $env:LOCALAPPDATA 'Programs\\FreeGen\\backend\\freegen.ico'; $desktop = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $desktop 'FreeGen.lnk')); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"' + $target + '\"'; $s.WorkingDirectory = $workDir; $s.IconLocation = $ico; $s.Save(); $smDir = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs'; if (-not (Test-Path $smDir)) { New-Item -ItemType Directory -Path $smDir -Force }; $s2 = $ws.CreateShortcut((Join-Path $smDir 'FreeGen.lnk')); $s2.TargetPath = 'wscript.exe'; $s2.Arguments = '\"' + $target + '\"'; $s2.WorkingDirectory = $workDir; $s2.IconLocation = $ico; $s2.Save()"

echo [*] Starting FreeGen...
start "" wscript.exe "%LOCALAPPDATA%\\Programs\\FreeGen\\FreeGen.vbs"
"""
    setup_bat.write_text(setup_bat_content, encoding="ansi")

    # 3. Create IExpress SED file
    sed_file = temp_dir / "installer.sed"
    sed_content = f"""[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=Do you want to install FreeGen V2.0?
DisplayLicense=
FinishMessage=FreeGen V2.0 installation complete!
TargetName={installer_exe}
FriendlyName=FreeGen Setup
AppLaunched=cmd.exe /c setup.bat
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=SourceFiles
[SourceFiles]
SourceFiles0={temp_dir}
[SourceFiles0]
%FILE0%=
%FILE1%=
[Strings]
FILE0="setup.bat"
FILE1="freegen_app.zip"
"""
    sed_file.write_text(sed_content, encoding="ansi")

    # 4. Compile with iexpress
    res = subprocess.run(["iexpress", "/N", str(sed_file)], capture_output=True, text=True)
    if res.returncode != 0 or not installer_exe.exists():
        print(f"[!] Warning: IExpress build returned {res.returncode}")
    else:
        print(f"[+] Single-file installer created at: {installer_exe}")

    # Clean up temp files
    shutil.rmtree(temp_dir, ignore_errors=True)

def create_zip():
    print("[*] Zipping application...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    
    shutil.make_archive(str(ZIP_PATH.with_suffix('')), 'zip', BUILDS_DIR, "FreeGen V2.0")
    print(f"[+] Zip created at: {ZIP_PATH}")

def main():
    BUILDS_DIR.mkdir(exist_ok=True)
    build_frontend()
    copy_files()
    create_scripts()
    create_launcher()
    create_installer()
    create_zip()
    print("\n[+] Build complete! FreeGen V2.0 installer and packages are ready in the 'builds' folder.")

if __name__ == "__main__":
    main()

