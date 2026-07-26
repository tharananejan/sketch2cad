from fastapi import APIRouter, HTTPException

from schemas.request import SupervisorRequest
from schemas.response import SupervisorResponse
from services.agent_logic import evaluate_complexity

# Initialize the router with a clean prefix
router = APIRouter(prefix="/supervisor", tags=["Complexity Checker Gateway"])


@router.post("/evaluate", response_model=SupervisorResponse)
async def evaluate_instruction(request: SupervisorRequest):
    """
    Receives user instructions and deterministically routes them to
    either the Simple or Complex execution paths.
    """
    try:
        routing_decision = evaluate_complexity(request)
        return routing_decision

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Supervisor evaluation failed: {str(e)}"
        )
