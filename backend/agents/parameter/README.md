# Parameter Agent

This agent extracts parameters and analyzes complexity from user prompts.

## What it does
- The Parameter Agent is a core component of the FreeGen system.
- It processes natural language prompts from the user.
- It intelligently extracts design parameters and dimensions.
- It determines the overall complexity of the requested design.
- It identifies any missing variables required to generate the model.
- **This agent asks questions back to the user if any parameters are missing for the requested CAD instruction.**
- It returns all this extracted information as structured JSON data.

## How it does it
- The agent exposes a FastAPI server with an `/analyze` endpoint.
- It loads a specialized system prompt from its local directory.
- It sends the user's prompt and the system prompt to a language model.
- It forces the model to respond strictly in a JSON object format.
- It parses the returned JSON string into a Python dictionary.
- It validates the data against a rigid schema before returning it to the caller.

## Technologies it uses
- **FastAPI**: Used to host the high-performance API server.
- **Groq LLM API**: Used for fast inference and intelligent parameter extraction.
- **Pydantic**: Used for strict data validation and schema definitions.
- **Python**: The core programming language for the agent's logic.
