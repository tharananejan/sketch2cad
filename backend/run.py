import subprocess
import sys
import time
import urllib.request
import urllib.error
import json
from pathlib import Path

CODE_GEN_URL = "http://127.0.0.1:8001/generate"
EXECUTION_URL = "http://127.0.0.1:8000/execute"

def process_instruction(step: str):
    print(f"\n[*] Generating code for: '{step}'...")
    req_gen = urllib.request.Request(
        CODE_GEN_URL,
        data=json.dumps({"step": step}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req_gen) as response:
            gen_data = json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"[!] Failed to reach Code Generator API: {e}")
        return

    code_array = gen_data.get("code", [])
    if not code_array or "step not available" in code_array:
        error = gen_data.get("error", "Unknown error generating code")
        print(f"[!] Code generation failed: {error}")
        return

    generated_code = "\n".join(code_array)
    print("\n--- Generated Code ---")
    print(generated_code)
    print("----------------------\n")

    print("[*] Sending to Execution Agent...")
    req_exec = urllib.request.Request(
        EXECUTION_URL,
        data=json.dumps({
            "step_id": 1,
            "code": generated_code
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req_exec) as response:
            exec_data = json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"[!] Failed to reach Execution API: {e}")
        return

    status = exec_data.get("status")
    print(f"\n[*] Execution Status: {status}")
    
    if status == "SUCCESS":
        print("[+] Code executed successfully in FreeCAD!")
        print("Stdout:", exec_data.get("stdout"))
    else:
        print("[-] Execution Failed!")
        print("Error Trace:\n", exec_data.get("error_trace"))

def main():
    backend_dir = Path(__file__).resolve().parent
    
    execution_dir = backend_dir / "agents" / "execution"
    code_gen_dir = backend_dir / "agents" / "code-generator"
    
    execution_python = execution_dir / ".venv" / "Scripts" / "python.exe"
    if not execution_python.exists():
        execution_python = sys.executable
        
    print("[*] Starting Execution Agent...")
    execution_process = subprocess.Popen(
        [str(execution_python), "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(execution_dir),
        stdout=subprocess.DEVNULL, # Hide server logs to keep terminal clean
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Starting Code Generator Agent...")
    code_gen_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "code-generator-router:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd=str(code_gen_dir),
        stdout=subprocess.DEVNULL, # Hide server logs to keep terminal clean
        stderr=subprocess.DEVNULL
    )
    
    print("[*] Waiting a few seconds for servers to start...")
    time.sleep(5)
    
    print("\n" + "="*50)
    print("🤖 Sketch2CAD Interactive Prompt Ready!")
    print("Type your CAD instructions below. Type 'exit' or 'quit' to close.")
    print("="*50 + "\n")
    
    try:
        while True:
            try:
                instruction = input("\nCAD Instruction > ").strip()
                if not instruction:
                    continue
                if instruction.lower() in ['exit', 'quit']:
                    break
                    
                process_instruction(instruction)
                
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\n")
    finally:
        print("[*] Shutting down background agents...")
        execution_process.terminate()
        code_gen_process.terminate()
        execution_process.wait()
        code_gen_process.wait()
        print("[+] Done!")

if __name__ == "__main__":
    main()
