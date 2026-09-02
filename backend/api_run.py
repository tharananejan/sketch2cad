import asyncio
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Load environment configuration
backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")
load_dotenv(find_dotenv())

# Import the Orchestrator
from orchestrator.router import AgentRouter

app = FastAPI(title="FreeGen WebSocket API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_PORTS = [38000, 38001, 38002, 38003, 38004]
processes: List[subprocess.Popen] = []


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "FreeGen"}


def kill_zombie_processes():
    """Kill any existing processes listening specifically on our agent API ports."""
    ports = AGENT_PORTS
    for port in ports:
        try:
            if sys.platform == "win32":
                output = subprocess.check_output(f'netstat -ano | findstr /R ":{port} "', shell=True).decode()
                for line in output.splitlines():
                    if "LISTENING" in line:
                        parts = line.strip().split()
                        pid = parts[-1]
                        if pid and pid != "0" and pid != str(os.getpid()):
                            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def is_port_open(port: int) -> bool:
    """Check if a port is actively accepting connections."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.15):
            return True
    except OSError:
        return False


def launch_services() -> List[subprocess.Popen]:
    """Launch the 5 microservice agents with environment propagation and non-blocking wait."""
    kill_zombie_processes()
    
    execution_dir = backend_dir / "agents" / "execution"
    code_gen_dir = backend_dir / "agents" / "code-generator"
    parameter_dir = backend_dir / "agents" / "parameter"
    supervisor_dir = backend_dir / "agents" / "supervisor"
    planner_dir = backend_dir / "agents" / "planner"
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    procs = []
    
    print("[*] Starting Execution Agent API (port 38000)...")
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "38000"],
        cwd=str(execution_dir),
        env=env,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ))
    
    print("[*] Starting Code Generator Agent API (port 38001)...")
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "code-generator-router:app", "--host", "127.0.0.1", "--port", "38001"],
        cwd=str(code_gen_dir),
        env=env,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ))
    
    print("[*] Starting Parameter Agent API (port 38002)...")
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "parameter-router:app", "--host", "127.0.0.1", "--port", "38002"],
        cwd=str(parameter_dir),
        env=env,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ))
    
    print("[*] Starting Supervisor Agent API (port 38003)...")
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "38003"],
        cwd=str(supervisor_dir),
        env=env,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ))
    
    print("[*] Starting Planner Agent API (port 38004)...")
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agents.planner.api:app", "--host", "127.0.0.1", "--port", "38004"],
        cwd=str(backend_dir),
        env=env,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ))
    
    return procs


@app.on_event("startup")
async def startup_event():
    global processes
    processes = launch_services()
    
    # Wait for all agent ports asynchronously without blocking the event loop
    deadline = time.monotonic() + 10.0
    for port in AGENT_PORTS:
        while time.monotonic() < deadline:
            if is_port_open(port):
                break
            await asyncio.sleep(0.2)
            
    print("\n" + "="*50)
    print("\033[96m[System] FreeGen Orchestrator WebSocket API Ready!\033[0m")
    print("="*50 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    global processes
    print("[*] Shutting down background APIs...")
    for p in processes:
        try:
            if sys.platform == "win32":
                subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=2)
        except Exception:
            pass
    kill_zombie_processes()
    print("[+] Done!")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    
    def status_callback(status_data: dict):
        asyncio.run_coroutine_threadsafe(websocket.send_json(status_data), loop)

    router = AgentRouter(status_callback=status_callback)

    import builtins
    import queue
    input_queue = queue.Queue()
    original_input = builtins.input
    original_print = builtins.print

    def ws_print(*args, **kwargs):
        original_print(*args, **kwargs)
        text = " ".join([str(a) for a in args])
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text).strip()
        
        if clean_text:
            msg_type = "agent"
            if clean_text.startswith("[Orchestrator]") or clean_text.startswith("==="):
                msg_type = "process"
            elif "Asks:" in clean_text or "?" in clean_text:
                msg_type = "question"
            elif clean_text.startswith("[Supervisor") or clean_text.startswith("[Parameter") or clean_text.startswith("[Planner") or clean_text.startswith("[Code Generator") or clean_text.startswith("[Execution"):
                msg_type = "agent"
            elif clean_text.startswith("[*]") or clean_text.startswith("[+]") or clean_text.startswith("[-]"):
                msg_type = "agent"
                
            asyncio.run_coroutine_threadsafe(websocket.send_json({"message": clean_text, "type": msg_type}), loop)

    def ws_input(prompt=""):
        if prompt:
            asyncio.run_coroutine_threadsafe(websocket.send_json({"state": "waiting for user input .."}), loop)
        return input_queue.get()

    is_waiting_for_input = False

    def run_router_thread(initial_data):
        nonlocal is_waiting_for_input
        builtins.print = ws_print
        builtins.input = ws_input
        try:
            router.run(initial_data)
        finally:
            builtins.print = original_print
            builtins.input = original_input
            is_waiting_for_input = False

    try:
        while True:
            data = await websocket.receive_text()
            if data:
                if is_waiting_for_input:
                    input_queue.put(data)
                else:
                    is_waiting_for_input = True
                    asyncio.create_task(asyncio.to_thread(run_router_thread, data))
                
    except WebSocketDisconnect:
        pass


# Mount frontend dist static files if present
dist_path = backend_dir.parent / "apps" / "web" / "dist"
if not dist_path.exists():
    dist_path = backend_dir / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=38080)


