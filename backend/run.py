import subprocess
import sys
import time
from pathlib import Path

# Import the new Orchestrator
from orchestrator.router import AgentRouter

def main():
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
        stdout=subprocess.DEVNULL, # Hide server logs to keep terminal clean
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
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Waiting a few seconds for servers to start...")
    time.sleep(5)
    
    # Initialize the router
    router = AgentRouter()
    
    print("\n" + "="*50)
    print("\033[96m[System] Sketch2CAD Orchestrator Ready!\033[0m")
    print("Type your CAD instructions below. Type 'exit' or 'quit' to close.")
    print("="*50 + "\n")
    
    try:
        while True:
            try:
                instruction = input("\n\033[1m\033[92mCAD Instruction > \033[0m").strip()
                if not instruction:
                    continue
                if instruction.lower() in ['exit', 'quit']:
                    break
                    
                # Run the orchestrator workflow for the given instruction
                router.run(instruction)
                
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\n")
    finally:
        print("[*] Shutting down background APIs...")
        execution_process.terminate()
        code_gen_process.terminate()
        parameter_process.terminate()
        supervisor_process.terminate()
        planner_process.terminate()
        
        execution_process.wait()
        code_gen_process.wait()
        parameter_process.wait()
        supervisor_process.wait()
        planner_process.wait()
        print("[+] Done!")

if __name__ == "__main__":
    main()
