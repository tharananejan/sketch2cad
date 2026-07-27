"""
Request schemas for the Code Generator Agent API.
"""

from pydantic import BaseModel, Field


class CodeGenerateRequest(BaseModel):
    """Payload representing a single CAD instruction step to be translated into code."""

    step: str = Field(
        ...,
        description="Natural language instruction or CAD step (e.g., 'make a cube of length 10mm').",
        examples=["make a cube of length 10mm", "create a cylinder with radius 5mm and height 20mm"],
    )
