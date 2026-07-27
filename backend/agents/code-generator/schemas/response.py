"""
Response schemas for the Code Generator Agent API.
"""

from pydantic import BaseModel, Field


class CodeGenerateResponse(BaseModel):
    """Payload representing the generated FreeCAD Python code and reference sources."""

    code: str = Field(
        ...,
        description="The generated FreeCAD Python script or command for the requested step.",
        examples=["import FreeCAD as App\nimport Part\ndoc = App.ActiveDocument\nbox = doc.addObject('Part::Box', 'Box')\nbox.Length = 10.0\ndoc.recompute()"],
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of knowledge base source files retrieved via RAG during generation.",
        examples=[["sample_freecad.txt"]],
    )
