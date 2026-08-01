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
