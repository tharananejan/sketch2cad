"""FastAPI boundary for running generated FreeCAD code in the local GUI."""

from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, StrictInt, StrictStr

from execution_router import execute_and_display

app = FastAPI(title="Sketch2CAD Execution Agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
class ExecuteRequest(BaseModel):
    """Code Generator to Execution Agent request contract."""

    step_id: StrictInt
    code: StrictStr


class ExecuteResponse(BaseModel):
    """Execution Agent response for the Error Handler or workflow caller."""

    step_id: int
    status: Literal["SUCCESS", "FAILED"]
    stdout: str
    error_trace: Optional[str]


@app.get("/health")
def health() -> dict:
    """Report that the HTTP execution service is running."""
    return {"status": "ok"}


@app.post("/execute", response_model=ExecuteResponse)
def execute_code(request: ExecuteRequest) -> ExecuteResponse:
    """Run generated code and open the resulting model in FreeCAD GUI on success."""
    result = execute_and_display(
        {"step_id": request.step_id, "code": request.code}
    )
    return ExecuteResponse(**result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
