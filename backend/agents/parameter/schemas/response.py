from typing import List, Dict, Optional
from pydantic import BaseModel

class AnalyzeResponse(BaseModel):
    is_complex: bool
    shape_detected: Optional[str] = None
    required_parameters: List[str]
    extracted_parameters: Dict[str, str]
    missing_parameters: List[str]
