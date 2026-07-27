"""FastAPI HTTP boundary for the Frontier Planning Agent."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from .dependencies import get_planner_service
from .errors import InvalidRequestError, PlannerError
from .models import PlanResponse, PlannerRequest
from .service import PlannerService

app = FastAPI(title="Sketch2CAD Frontier Planning Agent", version="1.0.0")


@app.get("/")
def read_root() -> HTMLResponse:
    """Expose a browser-friendly planner test page."""

    return HTMLResponse(_PLANNER_UI)


_PLANNER_UI = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sketch2CAD Frontier Planner</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7f9;
      color: #15171a;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 32px;
    }
    main {
      width: min(980px, 100%);
      background: white;
      border: 1px solid #d9dee7;
      border-radius: 8px;
      box-shadow: 0 12px 32px rgba(20, 25, 35, 0.08);
      overflow: hidden;
    }
    header {
      padding: 24px 28px;
      border-bottom: 1px solid #e5e9f0;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 24px;
      line-height: 1.25;
    }
    p {
      margin: 0;
      color: #586170;
      line-height: 1.5;
    }
    form {
      display: grid;
      gap: 16px;
      padding: 24px 28px;
    }
    label {
      display: grid;
      gap: 8px;
      font-weight: 650;
    }
    textarea, input {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid #c8d0dc;
      border-radius: 6px;
      padding: 12px 14px;
      font: inherit;
      color: #15171a;
      background: #fbfcfe;
    }
    textarea {
      min-height: 160px;
      resize: vertical;
    }
    button {
      justify-self: start;
      border: 0;
      border-radius: 6px;
      padding: 11px 18px;
      font: inherit;
      font-weight: 700;
      color: white;
      background: #1769e0;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.65;
      cursor: wait;
    }
    pre {
      margin: 0;
      min-height: 180px;
      padding: 20px 28px;
      overflow: auto;
      border-top: 1px solid #e5e9f0;
      background: #101418;
      color: #e8edf4;
      line-height: 1.5;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Sketch2CAD Frontier Planner</h1>
      <p>Paste a complex CAD design request. The planner returns modeling steps only.</p>
    </header>
    <form id="planner-form">
      <label>
        Design request
        <textarea id="request" required placeholder="Example: Design a wall-mounted enclosure with a removable lid and four mounting bosses."></textarea>
      </label>
      <label>
        Expected design context
        <input id="expected-design" placeholder="Optional: Wall-mounted electronics enclosure">
      </label>
      <button id="submit" type="submit">Generate Plan</button>
    </form>
    <pre id="output">Planner output will appear here.</pre>
  </main>
  <script>
    const form = document.getElementById("planner-form");
    const output = document.getElementById("output");
    const submit = document.getElementById("submit");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submit.disabled = true;
      output.textContent = "Planning...";

      const payload = {
        request: document.getElementById("request").value,
        context: {
          expected_design: document.getElementById("expected-design").value,
          completed_steps: [],
          remaining_steps: [],
          errors: []
        }
      };

      try {
        const response = await fetch("/planner", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        output.textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        output.textContent = JSON.stringify({ error: String(error) }, null, 2);
      } finally {
        submit.disabled = false;
      }
    });
  </script>
</body>
</html>"""


@app.exception_handler(PlannerError)
async def handle_planner_error(_: Request, error: PlannerError) -> JSONResponse:
    """Return all expected planner failures through the JSON error envelope."""

    return JSONResponse(status_code=error.status_code, content=error.to_payload())


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    """Convert FastAPI body validation errors into the planner error contract."""

    planner_error = InvalidRequestError(
        "The request body does not match the planner request schema.",
        details={"validation_errors": error.errors()},
    )
    return JSONResponse(status_code=planner_error.status_code, content=planner_error.to_payload())


@app.post("/planner", response_model=PlanResponse)
def create_plan(
    planner_request: PlannerRequest,
    service: PlannerService = Depends(get_planner_service),
) -> PlanResponse:
    """Generate a strict complex CAD plan for n8n orchestration."""

    return service.plan(planner_request)
