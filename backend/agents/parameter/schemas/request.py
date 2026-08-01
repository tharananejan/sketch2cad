from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    prompt: str
