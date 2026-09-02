from __future__ import annotations
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from .dependencies import get_planner_service
from .errors import InvalidRequestError, PlannerError
from .models import PlannerRequest, PlannerResponse
from .service import PlannerService

app = FastAPI(title="Sketch2CAD Frontier Planning Agent", version="1.0.0")


@app.exception_handler(PlannerError)
async def handle_planner_error(_: Request, error: PlannerError) -> JSONResponse:
    """Return all expected planner failures through the JSON error envelope."""
    payload = jsonable_encoder(error.to_payload())
    return JSONResponse(status_code=error.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    planner_error = InvalidRequestError(
        "The request body does not match the planner request schema.",
        details={"validation_errors": error.errors()},
    )
    payload = jsonable_encoder(planner_error.to_payload())
    return JSONResponse(status_code=planner_error.status_code, content=payload)


@app.post("/planner", response_model=PlannerResponse)
def create_plan(
    planner_request: PlannerRequest,
    service: PlannerService = Depends(get_planner_service),
) -> PlannerResponse:
    return service.plan(planner_request)
