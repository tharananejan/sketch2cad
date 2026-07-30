# Execution Agent

**Purpose:** Non-LLM Script Executor & Failure Listener.

Receives generated FreeCAD Python from the Code Generator through `POST /execute`. It first runs the code headlessly with FreeCADCmd to catch execution errors for the Error Handler. If that succeeds, it launches the same code as a `.FCMacro` in the local FreeCAD GUI, where the user sees the generated model.

Run locally after installing dependencies:

```powershell
& <python> -m pip install -r requirements.txt
& <python> -m uvicorn api:app --host 127.0.0.1 --port 8000
```
