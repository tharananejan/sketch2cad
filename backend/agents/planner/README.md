# Frontier Planning Agent

The Frontier Planning Agent converts already-classified **complex** Sketch2CAD requests into an ordered, implementation-agnostic CAD modeling plan. If CAD-critical parameters are missing, it asks structured follow-up questions before planning. It never writes Python, FreeCAD APIs, CAD syntax, executable scripts, or provider-specific logic into its plan output.

## Architecture

`POST /planner` calls `PlannerService`, which first audits parameters and only then asks for a CAD plan. The service owns validation, deterministic plan IDs, prompt construction, JSON parsing, pending-question gating, underspecified-prompt fallback questions, and output safety. Provider adapters own only HTTP transport.

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
    "parameter_answers": {},
    "pending_questions": []
  }
}
```

`context` is optional. Its fields default to an empty design description, empty arrays, an empty `parameter_answers` object, and empty `pending_questions`. Follow-up requests must keep the same design request, send the last returned questions as `pending_questions`, and add answers keyed by `parameter_id`.

Dimension answers must include a value and a user-selected unit. The browser UI renders dimension units as a dropdown with `mm`, `cm`, and `inch`; boolean questions are also rendered as dropdowns, not checkboxes.

```json
{
  "parameter_answers": {
    "side_length": {
      "value": 40,
      "unit": "mm"
    }
  }
}
```

## Response Schemas

Planned responses keep a flat `steps` array for downstream compatibility. Simple parts return only `steps` (empty `phases`); complex designs additionally group those same steps into construction `phases`, each with a goal and ordered steps. Step IDs are globally consecutive across the whole plan, and a planned response contains either `steps` or `phases`, never both.

Simple part shape:

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
      "category": "feature",
      "depends_on": []
    }
  ],
  "phases": []
}
```

Complex design shape (steps are flattened into `steps` for downstream consumers):

```json
{
  "status": "planned",
  "plan_id": "f1cf2bb2-7ea8-53d9-8616-9175c6f15dd9",
  "complexity": "complex",
  "steps": [
    {
      "step_id": 1,
      "title": "Establish enclosure envelope",
      "description": "Create the outer enclosure volume.",
      "category": "feature",
      "depends_on": []
    }
  ],
  "phases": [
    {
      "phase_id": 1,
      "title": "Envelope",
      "goal": "Define the outer enclosure volume and wall thickness.",
      "depends_on": [],
      "steps": [
        {
          "step_id": 1,
          "title": "Establish enclosure envelope",
          "description": "Create the outer enclosure volume.",
          "category": "feature",
          "depends_on": []
        }
      ]
    }
  ]
}
```

Step IDs must start at `1`, remain consecutive across the whole plan (including across phases), and depend only on earlier step IDs. Phase IDs must start at `1`, remain consecutive, and depend only on earlier phase IDs. The plan ID is deterministically derived from the request and context.

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
      "value_type": "dimension",
      "unit": null,
      "unit_options": ["mm", "cm", "inch"],
      "options": [],
      "reason": "A cube requires one equal side length.",
      "current_value": null,
      "issue": null
    }
  ]
}
```

## Parameter Follow-up Flow

The orchestrator should collect answers, place them in `context.parameter_answers`, include the returned questions in `context.pending_questions`, and call `/planner` again.

The planner has a strict gate before it can return `status: "planned"`:

1. If any pending question is unanswered, the response remains `needs_parameters` and the audit or planning model is not called.
2. If an answer is invalid, such as a non-positive dimension or a dimension without a unit, the response remains `needs_parameters` with an `issue` and `current_value` for that parameter only.
3. Once all pending answers are valid, the audit runs. If it discovers a new required parameter, only that new parameter is returned.
4. If an audit response repeats a parameter that already has a valid answer, the duplicate question is ignored. Explicit correction questions remain when the audit identifies a cross-parameter conflict.
5. The planning model runs only after the audit is ready and no missing or invalid parameters remain.

For example, a cube flow should preserve the supplied answer instead of asking for `side_length` again:

```json
{
  "request": "Generate a cube",
  "context": {
    "parameter_answers": {
      "side_length": {
        "value": 40,
        "unit": "mm"
      }
    },
    "pending_questions": [
      {
        "parameter_id": "side_length",
        "question": "What side length should the cube have?",
        "value_type": "dimension",
        "unit": null,
        "unit_options": ["mm", "cm", "inch"],
        "options": [],
        "reason": "A cube requires one equal side length."
      }
    ]
  }
}
```

The browser test UI preserves `pending_questions` and previously valid `parameter_answers` between follow-up requests. Its primary plan button is disabled while answers are pending; modifying the design request starts a new parameter-check cycle.

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

The dedicated prompts instruct the provider to think like a CAD engineer, preserve engineering intent, and first check for missing or invalid CAD-critical parameters. The audit prompt can return only `ready`, `needs_parameters`, or `unsupported`; the planning prompt runs only after audit readiness and can return only `planned` or `unsupported`. Both prompts explicitly ban Python, scripts, API calls, FreeCAD APIs, CAD syntax, macros, and explanatory prose.

The service first performs strict JSON parsing. If that fails, it makes one deterministic extraction-and-parse retry for fenced or prefixed JSON. A second failure returns `malformed_model_response`; it never invents a fallback plan.

## Provider Replacement

To add another provider, implement `LLMProvider.generate(system_prompt, user_prompt) -> str`, add a configuration branch in `dependencies.py`, and return the raw model message content. Do not place provider transport, credentials, or model selection in `PlannerService`.
