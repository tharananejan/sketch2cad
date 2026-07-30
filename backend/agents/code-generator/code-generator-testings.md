# Code Generator Agent Testing Procedures

This document provides a guide for testing the Code Generator Agent components, RAG retrieval thresholds, step availability validations, and API schemas on the testing laptop where Ollama is installed.

---

## 1. Prerequisites on the Testing Laptop

1. **Start Ollama** and ensure the necessary model and embedding weights are pulled:
   ```bash
   ollama pull qwen2.5-coder:0.5b
   ollama pull nomic-embed-text
   ```

2. **Navigate to the agent directory** and install the Python dependencies:
   ```bash
   cd backend/agents/code-generator
   pip install -r requirements.txt
   ```

---

## 2. Run the Automated Unit Tests

Run the built-in unit tests to verify that JSON schema validators, the error parser, and `"step not available"` validation operate correctly:

```bash
python test_code_generator.py
```

*Expected result: All tests pass successfully (`OK`).*

---

## 3. Start the API Server

Start the microservice HTTP router:

```bash
python code-generator-router.py
```
*The agent endpoint is now exposed locally at `http://localhost:8001/generate`.*

---

## 4. Manual API Test Cases

You can test endpoints using `curl` or any API client (e.g. Postman).

### Test Case A: Step WITH Available Knowledge (Valid Code Output)
Send a query step that has instructions in [sample_freecad.txt](knowledge_base/sample_freecad.txt):

```bash
curl -X POST "http://localhost:8001/generate" \
     -H "Content-Type: application/json" \
     -d '{"step": "make a cube (5mm,5mm,10mm)"}'
```

**Expected JSON Response:**
```json
{
  "code": "import FreeCAD as App\nimport Part\ndoc = App.ActiveDocument\nif doc is None:\n    doc = App.newDocument('Design')\nbox = doc.addObject('Part::Box', 'Box')\nbox.Length = 5.0\nbox.Width = 5.0\nbox.Height = 10.0\ndoc.recompute()",
  "sources": ["sample_freecad.txt"],
  "error": null
}
```

---

### Test Case B: Step WITHOUT Available Knowledge (Termination with Error)
Send a step that does not have knowledge in the reference base (e.g., drawing gears or complex shapes):

```bash
curl -X POST "http://localhost:8001/generate" \
     -H "Content-Type: application/json" \
     -d '{"step": "make a gear with 20 teeth and module 2mm"}'
```

**Expected JSON Response:**
```json
{
  "code": "step not available",
  "sources": [],
  "error": "step not available"
}
```

---

### Test Case C: Flexible JSON Inputs from Other Agents
upstream agents may send instructions under different keys (`instruction` or `input`). Verify that these formats are correctly mapped:

```bash
curl -X POST "http://localhost:8001/generate" \
     -H "Content-Type: application/json" \
     -d '{"instruction": "make a cyclinder(10,10,10)"}'
```

**Expected JSON Response:**
Returns the valid FreeCAD Cylinder creation code successfully.

---

## 5. Adding New Knowledge Steps
To add support for new instructions, simply create a new `.txt` or `.md` file inside the [knowledge_base/](knowledge_base/) directory containing relevant python macros. The agent will automatically ingest it on the next run.
