from fastapi import APIRouter, HTTPException
from backend.agents.supervisor.schemas.request import SupervisorRequest
from backend.agents.supervisor.schemas.response import SupervisorResponse
from backend.agents.supervisor.services.agent_logic import evaluate_complexity

# Initialize the router with a clean prefix
router = APIRouter(prefix="/supervisor", tags=["Complexity Checker Gateway"])

@router.post("/evaluate", response_model=SupervisorResponse)
async def evaluate_instruction(request: SupervisorRequest):
    """
    Receives user instructions and deterministically routes them to 
    either the Simple or Complex execution paths.
    """
    try:
        # Pass the validated JSON payload directly to your deterministic logic
        routing_decision = evaluate_complexity(request)
        return routing_decision
        
    except Exception as e:
        # Catch any unexpected errors and return a clean HTTP 500
        raise HTTPException(status_code=500, detail=f"Supervisor evaluation failed: {str(e)}")