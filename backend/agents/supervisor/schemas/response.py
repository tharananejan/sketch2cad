from pydantic import BaseModel, Field
from typing import Literal

class SupervisorResponse(BaseModel):
    routing_path: Literal["simple", "complex"] = Field(
        ..., 
        title="Routing Path",
        description="The flag telling n8n where to send the payload next."
    )
    original_instruction: str = Field(
        ...,
        title="Original Instruction",
        description="Passes the original prompt down the chain for the next agent to use."
    )