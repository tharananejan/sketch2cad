import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

from schemas.request import AnalyzeRequest
from schemas.response import AnalyzeResponse
from config import MODEL_NAME, TEMPERATURE

# Load environment variables from the agent's .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY environment variable is missing in the parameter agent's .env file.")

client = Groq(api_key=api_key)

def load_system_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError("System prompt file not found.")

def analyze_prompt(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Sends the user prompt to the Groq LLM to intelligently extract parameters,
    determine complexity, and identify missing required variables.
    """
    system_prompt = load_system_prompt()
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": request.prompt,
            }
        ],
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"}
    )
    
    response_content = chat_completion.choices[0].message.content
    try:
        data = json.loads(response_content)
        return AnalyzeResponse(**data)
    except Exception as e:
        # Fallback if something goes wildly wrong with parsing
        raise ValueError(f"Failed to parse LLM response: {e}\nResponse: {response_content}")
