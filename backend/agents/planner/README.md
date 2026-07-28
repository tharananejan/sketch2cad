# Frontier Planning Agent

The Frontier Planning Agent converts already-classified **complex** Sketch2CAD requests into an ordered, implementation-agnostic CAD modeling plan. If CAD-critical parameters are missing, it asks structured follow-up questions before planning. It never writes Python, FreeCAD APIs, CAD syntax, executable scripts, or provider-specific logic into its plan output.

## Architecture

`POST /planner` calls `PlannerService`, which builds the dedicated CAD-planning prompt, passes it to an injected `LLMProvider`, validates the returned JSON, and emits the strict public plan schema. The service owns validation, deterministic plan IDs, prompt construction, JSON parsing, and output safety. Provider adapters own only HTTP transport.

Development and test deployments use `GroqProvider`; production switches to `DeepSeekProvider` with configuration only. Both implement the same OpenAI-compatible `LLMProvider` interface. A new provider can be added without changing `PlannerService`.

The agent consumes the context supplied by n8n but never mutates context or shared files. The downstream Code Generation Agent receives only responses whose `status` is `planned`; `needs_parameters` responses must be routed back to the user for answers.

## Request Schema

```json
{
  "request": "Design a wall-mounted enclosure with a removable lid and four mounting bosses.",
  "context": {
    "expected_design": "Wall-mounted electronics enclosure",
    "completed_steps": [],
    "remaining_steps": [],
    "errors": [],
    "parameter_answers": {}
  }
}
```

`context` is optional. Its fields default to an empty design description, empty arrays, and an empty `parameter_answers` object. Follow-up requests should keep the same design request and add answers keyed by the returned `parameter_id`.

## Response Schemas

Planned responses are exactly this JSON shape:

```json
{
  "status": "planned",
  "plan_id": "f1cf2bb2-7ea8-53d9-8616-9175c6f15dd9",
  "complexity": "complex",
  "steps": [
    {
      "step_id": 1,
      "title": "Establish enclosure envelope",
      "description": "Create the outer enclosure volume using the required width, height, depth, and wall-thickness intent.",
      "depends_on": []
    }
  ]
}
```

Step IDs must start at `1`, remain consecutive, and depend only on earlier step IDs. The plan ID is deterministically derived from the request and context.

When CAD-critical details are missing, the planner returns questions instead of steps:

```json
{
  "status": "needs_parameters",
  "plan_id": "f1cf2bb2-7ea8-53d9-8616-9175c6f15dd9",
  "complexity": "complex",
  "questions": [
    {
      "parameter_id": "side_length",
      "question": "What side length should the cube have?",
      "value_type": "number",
      "unit": "mm",
      "options": [],
      "reason": "A cube requires one equal side length."
    }
  ]
}
```

The orchestrator should collect answers, place them in `context.parameter_answers`, and call `/planner` again.

## Error Schema

Failures use a non-2xx status and this JSON envelope:

```json
{
  "error": {
    "code": "malformed_model_response",
    "message": "The planner provider returned malformed JSON after one parse retry.",
    "details": {
      "parse_attempts": 2
    }
  }
}
```

The endpoint returns `422` for invalid or unsupported requests, `502` for provider and model-response failures, and `500` for invalid runtime configuration.

## Configuration

Copy `.env.example` values into the environment; never commit API keys.

| Setting | Purpose |
| --- | --- |
| `PLANNER_PROVIDER` | `groq` for development/testing, `deepseek` for production. Defaults to `groq`. |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL` | Required Groq credentials/model and optional endpoint override. |
| `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` | Required DeepSeek credentials/model and optional endpoint override. |
| `PLANNER_TIMEOUT_SECONDS` | Provider HTTP timeout; defaults to `30`. |
| `PLANNER_MAX_OUTPUT_TOKENS` | Maximum provider output tokens; defaults to `2048`. |

The selected provider uses temperature `0` and requests a JSON object response. Model identifiers remain configuration values so deployments can select approved provider models without changing planner logic.

## Run

Install the local package dependencies from this directory:

```powershell
python -m pip install -r requirements.txt
```

Start the endpoint from the repository root:

```powershell
python -m uvicorn backend.agents.planner.api:app --host 127.0.0.1 --port 8000
```

Send complex requests to `POST http://127.0.0.1:8000/planner`.

Run the focused test suite from the repository root:

```powershell
python -m pytest backend/agents/planner/tests
```

## Prompt Design

The dedicated prompt instructs the provider to think like a CAD engineer, preserve engineering intent, and first check for missing CAD-critical parameters. It requires JSON-only output and either a valid plan draft, a valid parameter-question draft, or an explicit unsupported declaration. It explicitly bans Python, scripts, API calls, FreeCAD APIs, CAD syntax, macros, and explanatory prose.

The service first performs strict JSON parsing. If that fails, it makes one deterministic extraction-and-parse retry for fenced or prefixed JSON. A second failure returns `malformed_model_response`; it never invents a fallback plan.

## Provider Replacement

To add another provider, implement `LLMProvider.generate(system_prompt, user_prompt) -> str`, add a configuration branch in `dependencies.py`, and return the raw model message content. Do not place provider transport, credentials, or model selection in `PlannerService`.
