import os
from typing import Dict, Optional
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from groq import Groq, GroqError, APIConnectionError, RateLimitError, AuthenticationError

from .config import MODEL_NAME, TEMPERATURE, MAX_TOKENS

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY environment variable is missing. Please set it in your .env file.")

client = Groq(api_key=api_key)

def ask_missing_parameter(shape: str, collected_parameters: Dict[str, str], missing_parameter: str) -> Optional[str]:
    """
    Uses Groq Cloud API to ask the user for a single missing parameter.
    
    Args:
        shape: The shape being created.
        collected_parameters: Parameters already collected.
        missing_parameter: The specific parameter to ask for.
        
    Returns:
        The generated question string from the LLM, or a fallback string on error.
    """
    
    system_prompt = """You are the Sketch2CAD Parameter Checking Agent.

Rules:
- Never generate CAD code.
- Never explain geometry.
- Ask only ONE missing parameter.
- Keep responses under 20 words.
- If all parameters exist, reply only COMPLETE."""

    user_prompt = f"""We are building a {shape}.
Collected parameters: {collected_parameters}
The missing parameter is: {missing_parameter}
Please ask the user for the {missing_parameter}."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return chat_completion.choices[0].message.content.strip()
    except AuthenticationError:
        return f"Authentication error: Invalid API key. Please check your GROQ_API_KEY. What is the {missing_parameter} for the {shape}?"
    except RateLimitError:
        return f"Rate limit exceeded. Please try again later. What is the {missing_parameter} for the {shape}?"
    except APIConnectionError:
        return f"Network error or timeout while connecting to Groq. What is the {missing_parameter} for the {shape}?"
    except GroqError as e:
        return f"Groq API is currently unavailable: {e}. What is the {missing_parameter} for the {shape}?"
    except Exception as e:
        return f"An unexpected error occurred: {e}. What is the {missing_parameter} for the {shape}?"
