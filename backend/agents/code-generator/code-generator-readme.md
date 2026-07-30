# Code Generator Agent

**Purpose:** Cloud Code Generation Agent (Qwen 2.5 Coder 32B via Groq API).

**Note:** Translates sequential text instructions and steps strictly into executable FreeCAD Python macros.

## Running Locally

To run the Code Generator agent locally:

1. Obtain a Groq API key and add it to the `.env` file at the root of the project:
```bash
# In your .env file
GROQ_API_KEY=your_groq_api_key_here
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
