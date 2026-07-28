# Code Generator Agent

**Purpose:** Local Code Generation Agent (Qwen 2.5 Coder 0.5B via Ollama).

**Note:** Translates sequential text instructions and steps strictly into executable FreeCAD Python macros.

## Running Locally

To run the Code Generator agent locally:

1. Ensure Ollama is installed, running, and the models are pulled:
```bash
ollama pull qwen2.5-coder:0.5b
ollama pull nomic-embed-text
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:
```bash
uvicorn code-generator-router:app --host 0.0.0.0 --port 8001
```

## Testing the Service

### PowerShell (Windows)
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8001/health"

# Test CAD code generation
Invoke-RestMethod -Uri "http://localhost:8001/generate" -Method Post -ContentType "application/json" -Body '{"step": "Create a cylinder with radius 10 and height 50"}'
```

### Git Bash / Linux / Mac (or curl.exe)
```bash
curl.exe -X POST http://localhost:8001/generate -H "Content-Type: application/json" -d "{\"step\": \"Create a cylinder with radius 10 and height 50\"}"
```
