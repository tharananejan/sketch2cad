from enum import Enum, auto
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class AgentState(Enum):
    PARAMETER_GATHERING = "PARAMETER_GATHERING"
    CODE_GENERATION = "CODE_GENERATION"
    EXECUTION = "EXECUTION"
    ERROR_HANDLING = "ERROR_HANDLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class OrchestratorContext(BaseModel):
    user_prompt: str
    current_state: AgentState = AgentState.PARAMETER_GATHERING
    
    # Parameter Agent State
    is_complex: Optional[bool] = None
    extracted_parameters: Dict[str, str] = Field(default_factory=dict)
    missing_parameters: List[str] = Field(default_factory=list)
    parameter_steps: List[str] = Field(default_factory=list)
    shape_type: Optional[str] = None
    
    # Code Generator State
    current_step_index: int = 0
    generated_code: str = ""
    
    # Execution State
    runned_codes: List[str] = Field(default_factory=list)
    failed_codes: List[str] = Field(default_factory=list)
    execution_errors: List[str] = Field(default_factory=list)
