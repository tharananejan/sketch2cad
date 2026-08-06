import asyncio
import subprocess
import sys
import time
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the new Orchestrator
from orchestrator.router import AgentRouter

app = FastAPI(title="Sketch2CAD WebSocket API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def launch_services():
    backend_dir = Path(__file__).resolve().parent
    
    execution_dir = backend_dir / "agents" / "execution"
    code_gen_dir = backend_dir / "agents" / "code-generator"
    parameter_dir = backend_dir / "agents" / "parameter"
    supervisor_dir = backend_dir / "agents" / "supervisor"
    planner_dir = backend_dir / "agents" / "planner"
    
    execution_python = execution_dir / ".venv" / "Scripts" / "python.exe"
    if not execution_python.exists():
        execution_python = sys.executable
        
    print("[*] Starting Execution Agent API...")
    execution_process = subprocess.Popen(
        [str(execution_python), "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(execution_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Starting Code Generator Agent API...")
    code_gen_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "code-generator-router:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd=str(code_gen_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Starting Parameter Agent API...")
    parameter_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "parameter-router:app", "--host", "127.0.0.1", "--port", "8002"],
        cwd=str(parameter_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Starting Supervisor Agent API...")
    supervisor_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8003"],
        cwd=str(supervisor_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Starting Planner Agent API...")
    planner_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agents.planner.api:app", "--host", "127.0.0.1", "--port", "8004"],
        cwd=str(backend_dir),
        stdout=subprocess.DEVNULL
    )
    
    print("[*] Waiting a few seconds for servers to start...")
    time.sleep(5)
    return [execution_process, code_gen_process, parameter_process, supervisor_process, planner_process]

processes = []

@app.on_event("startup")
async def startup_event():
    global processes
    processes = launch_services()
    print("\n" + "="*50)
    print("\033[96m[System] Sketch2CAD Orchestrator WebSocket API Ready!\033[0m")
    print("="*50 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    global processes
    print("[*] Shutting down background APIs...")
    for p in processes:
        p.terminate()
    for p in processes:
        p.wait()
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
    import re
    input_queue = queue.Queue()
    original_input = builtins.input
    original_print = builtins.print

    def ws_print(*args, **kwargs):
        original_print(*args, **kwargs)
        text = " ".join([str(a) for a in args])
        # Remove ANSI escape codes
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text).strip()
        
        if clean_text:
            msg_type = "agent"
            if clean_text.startswith("[") or clean_text.startswith("*") or clean_text.startswith("="):
                msg_type = "process"
            if "Asks:" in clean_text:
                msg_type = "question"
                
            asyncio.run_coroutine_threadsafe(websocket.send_json({"message": clean_text, "type": msg_type}), loop)

    def ws_input(prompt=""):
        if prompt:
            # Instead of sending the input prompt as a chat message, we send a status update
            # so the frontend can display 'waiting for user input ..' with the typing dots
            asyncio.run_coroutine_threadsafe(websocket.send_json({"state": "waiting for user input .."}), loop)
        # Block until a message is received from the queue
        return input_queue.get()

    # We track whether we are currently waiting for input so we don't start a new router run
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
                    # Run the synchronous router in a background thread without blocking the WebSocket event loop
                    asyncio.create_task(asyncio.to_thread(run_router_thread, data))
                
    except WebSocketDisconnect:
        print("Client disconnected")

# Mount built web frontend static files if available
from fastapi.staticfiles import StaticFiles
dist_path = Path(__file__).resolve().parent.parent / "apps" / "web" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)

