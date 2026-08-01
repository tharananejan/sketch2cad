import sys
import os

# We remove GROQ_API_KEY_PARAMETER if it exists to test the error handling
if 'GROQ_API_KEY_PARAMETER' in os.environ:
    del os.environ['GROQ_API_KEY_PARAMETER']

sys.path.append(r'd:\FreeCadAgent\sketch2cad\backend\agents')

try:
    from parameter.dialogue import ask_missing_parameter
    print("FAILED: Did not raise RuntimeError when API key is missing")
except RuntimeError as e:
    print("SUCCESS: Raised RuntimeError when API key is missing:")
    print(e)
except Exception as e:
    print(f"FAILED: Raised different exception: {e}")
