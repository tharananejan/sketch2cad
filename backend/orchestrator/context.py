from enum import Enum, auto
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentState(Enum):
    COMPLEXITY_CHECK = "COMPLEXITY_CHECK"
    PARAMETER_GATHERING = "PARAMETER_GATHERING"
    PLANNING = "PLANNING"
    CODE_GENERATION = "CODE_GENERATION"
    EXECUTION = "EXECUTION"
    ERROR_HANDLING = "ERROR_HANDLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class OrchestratorContext(BaseModel):
    user_prompt: str
    current_state: AgentState = AgentState.COMPLEXITY_CHECK
    
    # Global Session State (Persistent across runs)
    session_completed_steps: List[str] = Field(default_factory=list)
    
    # Parameter Agent State
    is_complex: Optional[bool] = None
    extracted_parameters: Dict[str, str] = Field(default_factory=dict)
    missing_parameters: List[str] = Field(default_factory=list)
    parameter_steps: List[str] = Field(default_factory=list)
    shape_type: Optional[str] = None
    
    # Planner Agent State
    planner_parameters: Dict[str, Any] = Field(default_factory=dict)
    planner_step_categories: List[str] = Field(default_factory=list)
    
    # Code Generator State
    current_step_index: int = 0
    generated_code: str = ""
    
    # Execution State
    runned_codes: List[str] = Field(default_factory=list)
    failed_codes: List[str] = Field(default_factory=list)
    execution_errors: List[str] = Field(default_factory=list)
