# Supervisor Agent

**Purpose:** Complexity Checker & Gateway Triage Router.

**Note:** Evaluates incoming text/sketch user inputs against a strict, hardcoded whitelist of primitive operations (e.g., "make a cube"). Routes whitelisted tasks to the Simple Path and unlisted/complex tasks to the Complex Path.

## API Endpoint ---this part not done!!!

**URL:** `http://localhost:8000/supervisor/evaluate`
**Method:** `POST`

## Request Schema (Input Contract)

Send this JSON payload from the n8n HTTP Request node:

```json
{
  "instruction": "make a cube with a width of 50mm",
  "canvas_data": null
}