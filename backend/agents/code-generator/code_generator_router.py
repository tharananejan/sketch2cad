"""
Code Generator Agent HTTP Router / API Server
Exposes FastAPI endpoints for n8n orchestration to generate FreeCAD Python code from CAD steps.
"""

from fastapi import FastAPI, APIRouter, Depends, HTTPException
import uvicorn

from deps import Settings, get_settings
from schemas.request import CodeGenerateRequest
from schemas.response import CodeGenerateResponse
from services.agent_logic import generate_cad_code

# Create APIRouter for integration into a multi-agent supervisor/gateway app
router = APIRouter(prefix="/code-generator", tags=["code-generator"])


@router.post("/generate", response_model=CodeGenerateResponse, summary="Generate FreeCAD Python code for a CAD step")
def generate_code(
    request: CodeGenerateRequest,
    settings: Settings = Depends(get_settings),
) -> CodeGenerateResponse:
    """
    Accepts a natural language instruction step and returns executable FreeCAD Python code
    along with RAG knowledge base citations.
    """
    if not request.step or not request.step.strip():
        raise HTTPException(status_code=400, detail="Instruction step cannot be empty.")

    code, sources = generate_cad_code(step=request.step, settings=settings)
    if isinstance(code, str) and code.strip().lower() == "step not available":
        return CodeGenerateResponse(code=["step not available"], sources=sources, error="step not available")
    elif isinstance(code, str):
        # Fallback if somehow it returns a single string
        return CodeGenerateResponse(code=[code], sources=sources)
    return CodeGenerateResponse(code=code, sources=sources)


@router.get("/health", summary="Health check endpoint")
def health_check():
    """Verify that the Code Generator service is running."""
    return {"status": "ok", "service": "code-generator"}


# Standalone FastAPI app instance for independent microservice deployment
app = FastAPI(
    title="sketch2cad — Code Generator Agent",
    description="Local SLM microservice for translating CAD instructions into FreeCAD Python scripting code.",
    version="1.0.0",
)
app.include_router(router)

# Also expose /generate at root level for flexibility in n8n webhook routing
@app.post("/generate", response_model=CodeGenerateResponse, tags=["default"])
def generate_code_root(
    request: CodeGenerateRequest,
    settings: Settings = Depends(get_settings),
) -> CodeGenerateResponse:
    return generate_code(request, settings)


@app.get("/health", tags=["default"])
def health_check_root():
    return health_check()


if __name__ == "__main__":
    uvicorn.run("code_generator_router:app", host="0.0.0.0", port=8001, reload=False)
