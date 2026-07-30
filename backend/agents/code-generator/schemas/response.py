"""
Response schemas for the Code Generator Agent API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CodeGenerateResponse(BaseModel):
    """Payload representing the generated FreeCAD Python code and reference sources."""

    code: list[str] = Field(
        ...,
        description="The generated FreeCAD Python script or command for the requested step, as an array of strings.",
        examples=[["import FreeCAD as App", "import Part", "doc = App.ActiveDocument", "box = doc.addObject('Part::Box', 'Box')", "box.Length = 10.0", "doc.recompute()"]],
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of knowledge base source files retrieved via RAG during generation.",
        examples=[["sample_freecad.txt"]],
    )
    error: Optional[str] = Field(
        None,
        description="Error message if the step is not available or generation failed.",
        examples=["step not available"],
    )
