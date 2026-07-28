"""FastAPI HTTP boundary for the Frontier Planning Agent."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from .dependencies import get_planner_service
from .errors import InvalidRequestError, PlannerError
from .models import PlannerRequest, PlannerResponse
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
    textarea, input, select {
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
    #questions-panel {
      display: none;
      padding: 24px 28px;
      border-top: 1px solid #e5e9f0;
      background: #fbfcfe;
    }
    #questions-panel h2 {
      margin: 0 0 16px;
      font-size: 18px;
      line-height: 1.3;
    }
    #questions-panel form {
      padding: 0;
    }
    .question-row {
      display: grid;
      gap: 6px;
    }
    .question-meta {
      color: #586170;
      font-size: 13px;
      line-height: 1.4;
    }
    .question-issue {
      color: #a13a16;
      font-size: 13px;
      line-height: 1.4;
      font-weight: 700;
    }
    .dimension-answer {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 120px;
      gap: 8px;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Sketch2CAD Frontier Planner</h1>
      <p>Paste a complex CAD design request. The planner returns modeling steps or parameter questions.</p>
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
    <section id="questions-panel" aria-live="polite"></section>
    <pre id="output">Planner output will appear here.</pre>
  </main>
  <script>
    const form = document.getElementById("planner-form");
    const output = document.getElementById("output");
    const submit = document.getElementById("submit");
    const questionsPanel = document.getElementById("questions-panel");
    let parameterAnswers = {};
    let pendingQuestions = [];
    let awaitingAnswers = false;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (awaitingAnswers) {
        output.textContent = "Answer the required parameters before generating a plan.";
        renderParameterQuestions(pendingQuestions);
        return;
      }
      parameterAnswers = {};
      pendingQuestions = [];
      await submitPlannerRequest();
    });

    for (const field of [document.getElementById("request"), document.getElementById("expected-design")]) {
      field.addEventListener("input", () => {
        if (!awaitingAnswers) {
          return;
        }
        awaitingAnswers = false;
        parameterAnswers = {};
        pendingQuestions = [];
        questionsPanel.style.display = "none";
        questionsPanel.replaceChildren();
        submit.disabled = false;
        output.textContent = "Design changed. Generate a plan to start the new parameter check.";
      });
    }

    async function submitPlannerRequest() {
      submit.disabled = true;
      questionsPanel.style.display = "none";
      questionsPanel.replaceChildren();
      output.textContent = "Planning...";

      const payload = {
        request: document.getElementById("request").value,
        context: {
          expected_design: document.getElementById("expected-design").value,
          completed_steps: [],
          remaining_steps: [],
          errors: [],
          parameter_answers: parameterAnswers,
          pending_questions: pendingQuestions
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
        if (data.status === "needs_parameters") {
          pendingQuestions = data.questions || [];
          awaitingAnswers = true;
          renderParameterQuestions(data.questions || []);
        } else if (data.status === "planned") {
          pendingQuestions = [];
          awaitingAnswers = false;
        }
      } catch (error) {
        output.textContent = JSON.stringify({ error: String(error) }, null, 2);
      } finally {
        submit.disabled = awaitingAnswers;
      }
    }

    function renderParameterQuestions(questions) {
      questionsPanel.style.display = "block";
      const heading = document.createElement("h2");
      heading.textContent = "Parameter answers";
      const answersForm = document.createElement("form");

      for (const question of questions) {
        const row = document.createElement("label");
        row.className = "question-row";
        row.textContent = question.question;

        const field = createAnswerField(question);
        row.appendChild(field);

        if (question.issue) {
          const issue = document.createElement("span");
          issue.className = "question-issue";
          issue.textContent = `Issue: ${question.issue}`;
          row.appendChild(issue);
        }

        const meta = document.createElement("span");
        meta.className = "question-meta";
        const unitText = question.unit ? ` Unit: ${question.unit}.` : "";
        const currentValueText = question.current_value !== null && question.current_value !== undefined
          ? ` Current value: ${formatCurrentValue(question.current_value)}.`
          : "";
        meta.textContent = `${question.reason}${unitText}${currentValueText}`;
        row.appendChild(meta);

        answersForm.appendChild(row);
      }

      const answerButton = document.createElement("button");
      answerButton.type = "submit";
      answerButton.textContent = "Submit Answers";
      answersForm.appendChild(answerButton);

      answersForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        parameterAnswers = { ...parameterAnswers, ...collectParameterAnswers(answersForm) };
        await submitPlannerRequest();
      });

      questionsPanel.replaceChildren(heading, answersForm);
    }

    function createAnswerField(question) {
      if (question.value_type === "dimension") {
        return createDimensionAnswerField(question);
      }

      if (question.value_type === "boolean") {
        return createBooleanAnswerField(question);
      }

      if (question.value_type === "choice") {
        const select = document.createElement("select");
        select.dataset.parameterId = question.parameter_id;
        select.required = true;
        for (const option of question.options || []) {
          const optionElement = document.createElement("option");
          optionElement.value = option;
          optionElement.textContent = option;
          select.appendChild(optionElement);
        }
        applyExistingScalarAnswer(select, question);
        return select;
      }

      const input = document.createElement("input");
      input.dataset.parameterId = question.parameter_id;
      input.required = true;
      if (question.value_type === "number" || question.value_type === "integer") {
        input.type = "number";
        input.step = question.value_type === "integer" ? "1" : "any";
      } else {
        input.type = "text";
      }
      applyExistingScalarAnswer(input, question);
      return input;
    }

    function createBooleanAnswerField(question) {
      const select = document.createElement("select");
      select.dataset.parameterId = question.parameter_id;
      select.dataset.answerKind = "boolean";
      select.required = true;

      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Select";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      for (const option of [
        { value: "true", label: "Yes" },
        { value: "false", label: "No" }
      ]) {
        const optionElement = document.createElement("option");
        optionElement.value = option.value;
        optionElement.textContent = option.label;
        select.appendChild(optionElement);
      }

      const existingAnswer = parameterAnswers[question.parameter_id] ?? question.current_value;
      if (typeof existingAnswer === "boolean") {
        select.value = existingAnswer ? "true" : "false";
      }
      return select;
    }

    function createDimensionAnswerField(question) {
      const group = document.createElement("div");
      group.className = "dimension-answer";

      const input = document.createElement("input");
      input.type = "number";
      input.step = "any";
      input.required = true;
      input.dataset.parameterId = question.parameter_id;
      input.dataset.answerKind = "dimension-value";

      const select = document.createElement("select");
      select.required = true;
      select.dataset.parameterId = question.parameter_id;
      select.dataset.answerKind = "dimension-unit";

      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Unit";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      for (const unit of question.unit_options || ["mm", "cm", "inch"]) {
        const optionElement = document.createElement("option");
        optionElement.value = unit;
        optionElement.textContent = unit;
        select.appendChild(optionElement);
      }

      applyExistingDimensionAnswer(input, select, question);
      group.append(input, select);
      return group;
    }

    function collectParameterAnswers(answersForm) {
      const answers = {};
      for (const field of answersForm.querySelectorAll("[data-answer-kind='dimension-value']")) {
        const parameterId = field.dataset.parameterId;
        const unitField = answersForm.querySelector(`[data-parameter-id="${parameterId}"][data-answer-kind="dimension-unit"]`);
        answers[parameterId] = {
          value: Number.parseFloat(field.value),
          unit: unitField ? unitField.value : ""
        };
      }

      for (const field of answersForm.querySelectorAll("[data-answer-kind='boolean']")) {
        answers[field.dataset.parameterId] = field.value === "true";
      }

      for (const field of answersForm.querySelectorAll("[data-parameter-id]:not([data-answer-kind])")) {
        const parameterId = field.dataset.parameterId;
        if (field.type === "number") {
          answers[parameterId] = field.step === "1" ? Number.parseInt(field.value, 10) : Number.parseFloat(field.value);
        } else {
          answers[parameterId] = field.value;
        }
      }
      return answers;
    }

    function applyExistingScalarAnswer(field, question) {
      const existingAnswer = parameterAnswers[question.parameter_id] ?? question.current_value;
      if (existingAnswer === null || existingAnswer === undefined) {
        return;
      }
      field.value = String(existingAnswer);
    }

    function applyExistingDimensionAnswer(input, select, question) {
      const existingAnswer = parameterAnswers[question.parameter_id] ?? question.current_value;
      if (existingAnswer === null || existingAnswer === undefined) {
        return;
      }
      if (typeof existingAnswer === "number") {
        input.value = String(existingAnswer);
        return;
      }
      if (typeof existingAnswer === "object") {
        if (existingAnswer.value !== undefined && existingAnswer.value !== null) {
          input.value = String(existingAnswer.value);
        }
        if (existingAnswer.unit) {
          select.value = existingAnswer.unit;
        }
      }
    }

    function formatCurrentValue(value) {
      if (value && typeof value === "object") {
        return JSON.stringify(value);
      }
      return String(value);
    }
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


@app.post("/planner", response_model=PlannerResponse)
def create_plan(
    planner_request: PlannerRequest,
    service: PlannerService = Depends(get_planner_service),
) -> PlannerResponse:
    """Generate a strict complex CAD plan for n8n orchestration."""

    return service.plan(planner_request)
