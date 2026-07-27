"""
Request schemas for the Code Generator Agent API.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


class CodeGenerateRequest(BaseModel):
    """Payload representing a single CAD instruction step to be translated into code."""

    step: str = Field(
        ...,
        description="Natural language instruction or CAD step (e.g., 'make a cube (5mm,5mm,10mm)').",
        examples=["make a cube (5mm,5mm,10mm)", "make a cyclinder(10,10,10)"],
    )

    @model_validator(mode="before")
    @classmethod
    def extract_step(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "step" not in values or not values.get("step"):
                for key in ["instruction", "input", "query", "cmd", "command"]:
                    if key in values and values[key]:
                        values["step"] = str(values[key])
                        break
                if ("step" not in values or not values.get("step")) and len(values) == 1:
                    val = next(iter(values.values()))
                    if isinstance(val, (str, dict, list)):
                        values["step"] = str(val)
        return values
