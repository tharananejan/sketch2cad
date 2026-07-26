from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any


class SupervisorRequest(BaseModel):
    instruction: str = Field(
        default="",
        title="User Instruction",
        description="The raw text command or description provided by the user.",
    )
    canvas_data: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Canvas Data",
        description="Optional JSON payload representing the 2d sketch from tldraw.",
    )

    @model_validator(mode="after")
    def require_instruction_or_canvas(self) -> "SupervisorRequest":
        has_instruction = bool(self.instruction and self.instruction.strip())
        has_canvas = bool(self.canvas_data)
        if not has_instruction and not has_canvas:
            raise ValueError(
                "At least one of 'instruction' (non-empty) or 'canvas_data' must be provided."
            )
        return self
