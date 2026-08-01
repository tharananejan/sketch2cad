from pydantic import BaseModel
from typing import Dict

class StartRequest(BaseModel):
    """Payload for the /start endpoint."""
    message: str

class ContinueRequest(BaseModel):
    """Payload for the /continue endpoint."""
    session_id: str
    message: str

class DialogueResponse(BaseModel):
    """Response returned when the dialogue is in progress."""
    session_id: str
    reply: str
    status: str

class CompleteResponse(BaseModel):
    """Response returned when all parameters have been collected."""
    status: str = "complete"
    shape: str
    parameters: Dict[str, str]
