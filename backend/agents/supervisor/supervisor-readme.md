# Supervisor Agent

**Purpose:** Complexity Checker & Gateway Triage Router.

**Note:** Evaluates incoming text/sketch user inputs against a strict, hardcoded whitelist of primitive operations (e.g., "make a cube"). Routes whitelisted tasks to the Simple Path and unlisted/complex tasks to the Complex Path.

## Local Run Instructions

```bash
cd backend/agents/supervisor
pip install -r requirements.txt
export GROQ_API_KEY="your_groq_api_key_here"  # Or set in .env file
uvicorn main:app --reload --port 8000
```


Service base URL: `http://localhost:8000`

## API Endpoint

**URL:** `http://localhost:8000/supervisor/evaluate`  
**Method:** `POST`

## Request Schema (Input Contract)

Send this JSON payload from the n8n HTTP Request node:

```json
{
  "instruction": "make a cube with a width of 50mm",
  "canvas_data": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instruction` | string | one of instruction / canvas_data | Raw text command (defaults to `""`) |
| `canvas_data` | object \| null | one of instruction / canvas_data | Optional tldraw sketch JSON |

At least one of a non-empty `instruction` or a non-null/non-empty `canvas_data` must be provided.

## Response Schema (Output Contract)

```json
{
  "routing_path": "simple",
  "original_instruction": "make a cube with a width of 50mm"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `routing_path` | `"simple"` \| `"complex"` | Flag telling n8n where to send the payload next |
| `original_instruction` | string | Original prompt passed downstream unchanged |

### Simple path example

Request:
```json
{ "instruction": "make a cube with a width of 50mm", "canvas_data": null }
```

Response:
```json
{
  "routing_path": "simple",
  "original_instruction": "make a cube with a width of 50mm"
}
```

### Complex path example

Request:
```json
{ "instruction": "design a bracket with mounting holes", "canvas_data": null }
```

Response:
```json
{
  "routing_path": "complex",
  "original_instruction": "design a bracket with mounting holes"
}
```

### Sketch-only example (routes complex)

Request:
```json
{ "instruction": "", "canvas_data": { "shapes": [] } }
```

Response:
```json
{
  "routing_path": "complex",
  "original_instruction": ""
}
```


## Routing Rules

| Condition | `routing_path` | Next agent |
|-----------|----------------|------------|
| Instruction contains a whitelisted primitive (word-boundary match) | `simple` | Parameter Agent |
| No primitive match (unmatched text, sketch-only, or sketch + complex text) | `complex` | Planner Agent |

**Whitelist:** `cube`, `cylinder`, `sphere`, `cone`, `box`, `torus`

Text with a matched primitive wins over canvas data (routes `simple`). Matching uses word boundaries so `"toolbox"` does not match `"box"`.

## Error Responses

| Status | When |
|--------|------|
| `422` | Validation error — both `instruction` empty and `canvas_data` missing/empty |
| `500` | Unexpected internal failure during evaluation |

## n8n Integration Notes

1. **HTTP Request** node → `POST http://localhost:8000/supervisor/evaluate` with the request JSON body.
2. **Switch** node on `$json.routing_path`:
   - `simple` → Parameter Agent
   - `complex` → Planner Agent
3. Forward `matched_primitive` and `original_instruction` to the downstream agent as needed.

## Tests

```bash
cd backend/agents/supervisor
python -m pytest tests/
```
