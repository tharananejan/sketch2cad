import uuid
from typing import Dict, Any, Optional

class SessionManager:
    """Manages conversational state for the parameter agent in memory."""
    def __init__(self):
        # Format: { session_id: { "shape": "", "parameters": {}, "missing": [], "history": [] } }
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        """Creates a new session and returns the session_id."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "shape": "",
            "parameters": {},
            "missing": [],
            "history": []
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an existing session by ID."""
        return self._sessions.get(session_id)
        
    def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Updates the session with new data."""
        if session_id in self._sessions:
            self._sessions[session_id].update(data)
            
    def add_to_history(self, session_id: str, role: str, content: str) -> None:
        """Appends a message to the session's history."""
        if session_id in self._sessions:
            self._sessions[session_id]["history"].append({"role": role, "content": content})
            
    def delete_session(self, session_id: str) -> None:
        """Deletes a session once complete or invalidated."""
        if session_id in self._sessions:
            del self._sessions[session_id]

# Global instance for dependency injection/usage in routes
session_manager = SessionManager()
