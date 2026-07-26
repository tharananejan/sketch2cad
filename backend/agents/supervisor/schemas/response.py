from pydantic import BaseModel, Field
from typing import Literal, Optional

class SupervisorResponse(BaseModel):
    routing_path: Literal["simple", "complex"] = Field(
        ..., 
        title="Routing Path",
        description="The deterministic flag telling n8n where to send the payload next."
    )
    matched_primitive: Optional[str] = Field(
        default=None,
        title="Matched Primitive",
        description="If the path is 'simple', this stores the identified shape (e.g., 'cube', 'cylinder')."
    )
    original_instruction: str = Field(
        ...,
        title="Original Instruction",
        description="Passes the original prompt down the chain for the next agent to use."
    )