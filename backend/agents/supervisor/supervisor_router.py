from fastapi import APIRouter, HTTPException
from schemas.request import SupervisorRequest
from schemas.response import SupervisorResponse
from services.agent_logic import evaluate_complexity

router = APIRouter(prefix="/supervisor", tags=["Complexity Checker Gateway"])

@router.post("/evaluate", response_model=SupervisorResponse)
async def evaluate_instruction(request: SupervisorRequest):
    try:
        # Await the LLM evaluation
        routing_decision = await evaluate_complexity(request)
        return routing_decision
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supervisor LLM evaluation failed: {str(e)}")