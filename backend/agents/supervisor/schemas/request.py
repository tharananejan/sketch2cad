from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class SupervisorRequest(BaseModel):
    instruction: str = Field(
        ...,
        title = "User Instruction",
        description = "The raw text command or description provided by the user."
    )
    canvas_data: OPtional[Dict[str, Any]] = Field(
        default = None,
        title = "Canvas Data",
        description = "Optional JSON payload representing the 2d sketch from tldraw."
    )