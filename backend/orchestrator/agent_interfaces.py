import sys
import os
import re
import urllib.request
import urllib.error
import json
from typing import Any, Dict, Optional

from .context import OrchestratorContext, AgentState

# ---------------------------------------------------------------------------
# Helpers for parsing dimension values from raw user input
# ---------------------------------------------------------------------------

_DIMENSION_RE = re.compile(
    r"^\s*([\d]+(?:[\.,][\d]+)?)\s*(mm|cm|inch|in|inches|m|ml|l)\s*$",
    re.IGNORECASE,
)

_UNIT_ALIASES: Dict[str, str] = {
    "mm": "mm",
    "cm": "cm",
    "m": "cm",        # convert m -> cm for the planner (value * 100)
    "inch": "inch",
    "in": "inch",
    "inches": "inch",
    "ml": "mm",       # capacity values stored as mm-equivalent
    "l": "mm",        # capacity values stored as mm-equivalent
}

_UNIT_SCALE: Dict[str, float] = {
    "m": 100.0,       # 1m = 100cm
    "l": 1000.0,      # 1L = 1000ml (stored as raw value, unit='mm' as placeholder)
}


def _parse_dimension_input(raw: str) -> Dict[str, Any] | str:
    """Convert raw user input like '10cm' into a DimensionAnswer dict.

    Returns ``{"value": float, "unit": str}`` for parseable dimensions.
    Falls back to the raw string for unparseable input.
    """
    match = _DIMENSION_RE.match(raw)
    if not match:
        # Try bare number — default to mm
        try:
            value = float(raw.replace(",", "."))
            return {"value": value, "unit": "mm"}
        except ValueError:
            return raw

    value = float(match.group(1).replace(",", "."))
    raw_unit = match.group(2).lower()
    canonical_unit = _UNIT_ALIASES.get(raw_unit, "mm")
    scale = _UNIT_SCALE.get(raw_unit, 1.0)
    return {"value": value * scale, "unit": canonical_unit}


# Regex to find dimension patterns in a user's natural-language prompt
_PROMPT_DIM_PATTERNS = [
    # "width of 10 mm", "height of 20cm"
    re.compile(
        r"(width|height|depth|radius|diameter|length|thickness|clearance)"
        r"\s+(?:of\s+)?([\d]+(?:[\.,][\d]+)?)\s*(mm|cm|inch|in)",
        re.IGNORECASE,
    ),
    # "10mm width", "20 cm height"
    re.compile(
        r"([\d]+(?:[\.,][\d]+)?)\s*(mm|cm|inch|in)\s+"
        r"(width|height|depth|radius|diameter|length|thickness|clearance)",
        re.IGNORECASE,
    ),
]


def _extract_prompt_dimensions(prompt: str) -> Dict[str, Any]:
    """Pre-extract dimension values from the user's prompt text.

    Returns a dict keyed by parameter name (e.g., ``width``) with
    ``DimensionAnswer``-shaped values.
    """
    extracted: Dict[str, Any] = {}
    for pattern in _PROMPT_DIM_PATTERNS:
        for match in pattern.finditer(prompt):
            groups = match.groups()
            if len(groups) == 3:
                # Determine which group is the name and which is the number
                if groups[0][0].isdigit():
                    # Pattern 2: number, unit, name
                    value_str, unit_str, name = groups
                else:
                    # Pattern 1: name, number, unit
                    name, value_str, unit_str = groups

                name_key = name.lower().strip()
                value = float(value_str.replace(",", "."))
                canonical_unit = _UNIT_ALIASES.get(unit_str.lower(), "mm")
                extracted[name_key] = {"value": value, "unit": canonical_unit}
    return extracted


def _format_parameters_block(parameters: Dict[str, Any]) -> str:
    """Format resolved parameters into a text block for the code generator."""
    if not parameters:
        return ""
    lines = ["\n--- Resolved Design Parameters ---"]
    for key, val in parameters.items():
        if isinstance(val, dict) and "value" in val and "unit" in val:
            lines.append(f"  {key}: {val['value']} {val['unit']}")
        else:
            lines.append(f"  {key}: {val}")
    lines.append("--- End Parameters ---")
    return "\n".join(lines)

class BaseAgentInterface:
    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        raise NotImplementedError("Agents must implement the process method.")

class SupervisorAgentInterface(BaseAgentInterface):
    """
    Interface for the Supervisor Agent (Complexity Checker).
    """
    def __init__(self, url: str = "http://127.0.0.1:8003/supervisor/evaluate"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        print(f"\n\033[94m[Supervisor Agent]\033[0m Checking complexity for: '{context.user_prompt}'")
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps({"instruction": context.user_prompt}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                analysis = json.loads(response.read().decode())
                routing_path = analysis.get("routing_path")
                
                if routing_path == "complex":
                    print("\033[93m[*] Detected a complex operation. Routing to Planner Agent.\033[0m")
                    context.is_complex = True
                    context.current_state = AgentState.PLANNING
                else:
                    print("\033[92m[*] Detected a simple operation. Routing to Parameter Agent.\033[0m")
                    context.is_complex = False
                    context.current_state = AgentState.PARAMETER_GATHERING
                    
        except urllib.error.URLError as e:
            print(f"\033[91m[!] Failed to reach Supervisor API: {e}\033[0m")
            context.execution_errors.append(str(e))
            context.current_state = AgentState.ERROR_HANDLING
            
        return context

class ParameterAgentInterface(BaseAgentInterface):
    """
    Interface for the LLM-driven Parameter Agent.
    """
    def __init__(self, url: str = "http://127.0.0.1:8002/analyze"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        print(f"\n\033[94m[Parameter Agent]\033[0m Analyzing prompt: '{context.user_prompt}'")
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps({"prompt": context.user_prompt}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                analysis = json.loads(response.read().decode())
                
                context.shape_type = analysis.get("shape_detected")
                if context.shape_type:
                    print(f"\033[94m[*] Detected Shape:\033[0m {context.shape_type}")
                    
                context.extracted_parameters = analysis.get("extracted_parameters", {})
                if context.extracted_parameters:
                    print(f"\033[94m[*] Extracted from prompt:\033[0m {context.extracted_parameters}")
                    
                missing = analysis.get("missing_parameters", [])
                
                # Interactive Loop
                while missing:
                    current_missing = missing[0]
                    
                    # Hardcoded question generation by Orchestrator
                    question = f"What is the {current_missing} of the {context.shape_type}?"
                    print(f"\n\033[96m[Parameter Agent] Asks:\033[0m \033[93m{question}\033[0m")
                    
                    try:
                        user_answer = input("\033[92mYour Answer > \033[0m").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\n\033[91m[!] Input interrupted. Aborting.\033[0m")
                        context.current_state = AgentState.FAILED
                        return context
                        
                    if not user_answer:
                        print("\033[91m[!] Please provide an answer.\033[0m")
                        continue
                        
                    # Send the updated prompt to the LLM to extract the missing parameter
                    updated_prompt = f"The {current_missing} is {user_answer}."
                    
                    # Call API to analyze the answer
                    ans_req = urllib.request.Request(
                        self.url,
                        data=json.dumps({"prompt": updated_prompt}).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    
                    try:
                        with urllib.request.urlopen(ans_req) as ans_res:
                            ans_analysis = json.loads(ans_res.read().decode())
                            new_extracted = ans_analysis.get("extracted_parameters", {})
                            
                            # Update context with anything new found
                            for k, v in new_extracted.items():
                                context.extracted_parameters[k] = v
                                print(f"\033[94m[*] Extracted {k}:\033[0m {v}")
                                
                            # If the specific parameter we asked for was found, remove it from missing
                            if current_missing in context.extracted_parameters:
                                missing.pop(0)
                            else:
                                print("\033[91m[-] Could not understand the value. Let's try again.\033[0m")
                                
                    except urllib.error.URLError as e:
                        print(f"\033[91m[!] Failed to reach Parameter API during answer extraction: {e}\033[0m")
                        context.current_state = AgentState.ERROR_HANDLING
                        return context
                        
                print("\n\033[92m[+] All parameters collected:\033[0m", context.extracted_parameters)
                
                # Generate step
                param_str = ", ".join([f"{k} {v}" for k, v in context.extracted_parameters.items()])
                step_instruction = f"make a {context.shape_type} with {param_str}"
                context.parameter_steps = [step_instruction]
                
                print(f"\033[94m[*] Generated Step:\033[0m '{step_instruction}'")
                context.current_state = AgentState.CODE_GENERATION
                
        except urllib.error.URLError as e:
            print(f"\033[91m[!] Failed to reach Parameter Agent API: {e}\033[0m")
            context.execution_errors.append(str(e))
            context.current_state = AgentState.ERROR_HANDLING
            
        return context

class PlannerAgentInterface(BaseAgentInterface):
    """
    Interface for the Frontier Planning Agent.
    Handles dimension answer formatting, pending_questions forwarding, and round caps.
    """
    MAX_PLANNER_ROUNDS = 3

    def __init__(self, url: str = "http://127.0.0.1:8004/planner"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        print(f"\n\033[95m[Planner Agent]\033[0m Planning steps for: '{context.user_prompt}'...")
        
        # Pre-extract dimensions that are already present in the user's prompt text
        new_parameter_answers: Dict[str, Any] = _extract_prompt_dimensions(context.user_prompt)
        
        # Merge with existing parameters in context
        parameter_answers = {**context.planner_parameters, **new_parameter_answers}
        
        if new_parameter_answers:
            extracted_names = ", ".join(f"{k}={v}" for k, v in new_parameter_answers.items())
            print(f"\033[94m[*] Pre-extracted from prompt:\033[0m {extracted_names}")

        pending_questions: list = []
        round_count = 0
        
        while True:
            round_count += 1
            if round_count > self.MAX_PLANNER_ROUNDS:
                print(f"\033[93m[!] Reached max {self.MAX_PLANNER_ROUNDS} planner rounds. Proceeding with current parameters.\033[0m")
                # Force planning by clearing pending_questions
                pending_questions = []
            
            payload = {
                "request": context.user_prompt,
                "context": {
                    "parameter_answers": parameter_answers,
                    "completed_steps": context.session_completed_steps,
                    "remaining_steps": [],
                    "errors": [],
                    "pending_questions": pending_questions,
                }
            }
            print(f"DEBUG: sending payload to planner: {payload}")
            
            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode())
                    status = res_data.get("status")
                    
                    if status == "needs_parameters":
                        # If we already hit the round cap, proceed with what we have
                        if round_count > self.MAX_PLANNER_ROUNDS:
                            print("\033[93m[!] Planner still wants parameters but round cap reached. Proceeding with available parameters.\033[0m")
                            break
                        
                        questions = res_data.get("questions", [])
                        for q in questions:
                            q_id = q.get("parameter_id")
                            q_text = q.get("question")
                            reason = q.get("reason", "")
                            value_type = q.get("value_type", "string")
                            issue = q.get("issue")
                            default = q.get("default")
                            
                            # Skip if we already have a valid answer
                            if q_id in parameter_answers and not issue:
                                continue
                                
                            print(f"\n\033[96m[Planner Agent] Asks:\033[0m \033[93m{q_text}\033[0m")
                            if reason:
                                print(f"\033[90m({reason})\033[0m")
                            if issue:
                                print(f"\033[91m  Issue: {issue}\033[0m")
                            if default is not None:
                                print(f"\033[90m  Default: {default}\033[0m")
                                
                            try:
                                user_answer = input("\033[92mYour Answer > \033[0m").strip()
                            except (EOFError, KeyboardInterrupt):
                                print("\n\033[91m[!] Input interrupted. Aborting.\033[0m")
                                context.current_state = AgentState.FAILED
                                return context
                            
                            # Use default if user provides empty answer
                            if not user_answer and default is not None:
                                user_answer = str(default)
                                print(f"\033[90m  Using default: {user_answer}\033[0m")
                            elif not user_answer:
                                print("\033[91m[!] Please provide an answer.\033[0m")
                                continue
                            
                            # Parse the answer into the correct format
                            if value_type == "dimension":
                                parameter_answers[q_id] = _parse_dimension_input(user_answer)
                            elif value_type == "number":
                                try:
                                    parameter_answers[q_id] = float(user_answer)
                                except ValueError:
                                    parameter_answers[q_id] = user_answer
                            elif value_type == "integer":
                                try:
                                    parameter_answers[q_id] = int(user_answer)
                                except ValueError:
                                    parameter_answers[q_id] = user_answer
                            elif value_type == "boolean":
                                parameter_answers[q_id] = user_answer.lower() in ("true", "yes", "1", "y")
                            else:
                                parameter_answers[q_id] = user_answer
                        
                        # Save returned questions as pending_questions for the next round
                        pending_questions = questions
                        continue
                        
                    elif status == "planned":
                        steps = res_data.get("steps", [])
                        phases = res_data.get("phases", [])
                        
                        # Flatten steps if phases exist
                        flat_steps = []
                        if phases:
                            for phase in phases:
                                flat_steps.extend(phase.get("steps", []))
                        else:
                            flat_steps = steps
                            
                        print("\033[92m[+] Planner successfully generated steps:\033[0m")
                        context.parameter_steps = []
                        context.planner_step_categories = []
                        context.planner_parameters = parameter_answers
                        
                        for i, step in enumerate(flat_steps):
                            step_text = step.get("description", step.get("title", ""))
                            step_category = step.get("category", "primitive")
                            print(f"  {i+1}. [{step_category}] {step_text}")
                            context.parameter_steps.append(step_text)
                            context.planner_step_categories.append(step_category)
                            
                        context.current_state = AgentState.CODE_GENERATION
                        return context
                        
                    else:
                        print(f"\033[91m[!] Unknown Planner Status: {status}\033[0m")
                        context.current_state = AgentState.ERROR_HANDLING
                        return context
                        
            except urllib.error.HTTPError as e:
                print(f"\033[91m[!] Failed to reach Planner API: HTTP Error {e.code}: {e.reason}\033[0m")
                print(f"\033[91m[!] Response Body: {e.read().decode('utf-8')}\033[0m")
                context.execution_errors.append(str(e))
                context.current_state = AgentState.ERROR_HANDLING
                return context
            except urllib.error.URLError as e:
                print(f"\033[91m[!] Failed to reach Planner API: {e}\033[0m")
                context.execution_errors.append(str(e))
                context.current_state = AgentState.ERROR_HANDLING
                return context

        # Fallback: round cap was reached. Make one final call with empty
        # pending_questions to force the planner past audit into planning.
        print("\033[93m[!] Forcing planning with collected parameters...\033[0m")
        fallback_payload = {
            "request": context.user_prompt,
            "context": {
                "parameter_answers": parameter_answers,
                "completed_steps": context.session_completed_steps,
                "remaining_steps": [],
                "errors": [],
                "pending_questions": [],
            }
        }
        fallback_req = urllib.request.Request(
            self.url,
            data=json.dumps(fallback_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(fallback_req) as response:
                res_data = json.loads(response.read().decode())
                status = res_data.get("status")

                if status == "planned":
                    steps = res_data.get("steps", [])
                    phases = res_data.get("phases", [])
                    flat_steps = []
                    if phases:
                        for phase in phases:
                            flat_steps.extend(phase.get("steps", []))
                    else:
                        flat_steps = steps

                    print("\033[92m[+] Planner successfully generated steps (after round cap):\033[0m")
                    context.parameter_steps = []
                    context.planner_step_categories = []
                    context.planner_parameters = parameter_answers

                    for i, step in enumerate(flat_steps):
                        step_text = step.get("description", step.get("title", ""))
                        step_category = step.get("category", "primitive")
                        print(f"  {i+1}. [{step_category}] {step_text}")
                        context.parameter_steps.append(step_text)
                        context.planner_step_categories.append(step_category)

                    context.current_state = AgentState.CODE_GENERATION
                    return context
                else:
                    print(f"\033[91m[!] Planner could not produce a plan even after round cap. Status: {status}\033[0m")
                    context.current_state = AgentState.ERROR_HANDLING
                    return context

        except urllib.error.URLError as e:
            print(f"\033[91m[!] Failed to reach Planner API during fallback: {e}\033[0m")
            context.execution_errors.append(str(e))
            context.current_state = AgentState.ERROR_HANDLING
            return context

class CodeGeneratorAgentInterface(BaseAgentInterface):
    """
    Interface for the lightweight SLM Code Generator Agent.
    Enriches step text with resolved parameters and skips non-executable planning steps.
    """
    def __init__(self, url: str = "http://127.0.0.1:8001/generate"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        if context.current_step_index >= len(context.parameter_steps):
            context.current_state = AgentState.COMPLETED
            return context
        
        step = context.parameter_steps[context.current_step_index]
        
        # Check step category — skip "planning" steps (math calculations)
        # that have no geometry to execute
        step_category = ""
        if context.current_step_index < len(context.planner_step_categories):
            step_category = context.planner_step_categories[context.current_step_index]
        
        if step_category == "planning":
            print(f"\n\033[90m[Code Generator Agent] Skipping planning step: '{step}'\033[0m")
            context.current_step_index += 1
            # Check if more steps remain
            if context.current_step_index < len(context.parameter_steps):
                context.current_state = AgentState.CODE_GENERATION
            else:
                context.current_state = AgentState.COMPLETED
            return context
        
        # Enrich step text with resolved parameters so the code generator
        # has concrete numeric values available
        enriched_step = step
        if context.planner_parameters:
            enriched_step = step + _format_parameters_block(context.planner_parameters)
        
        print(f"\n\033[95m[Code Generator Agent]\033[0m Generating code for step: '{step}'...")
        
        req_gen = urllib.request.Request(
            self.url,
            data=json.dumps({"step": enriched_step}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req_gen) as response:
                gen_data = json.loads(response.read().decode())
                
                code_array = gen_data.get("code", [])
                if not code_array or "step not available" in code_array:
                    error = gen_data.get("error", "Unknown error generating code")
                    print(f"\033[91m[!] Code generation failed: {error}\033[0m")
                    context.current_state = AgentState.ERROR_HANDLING
                    context.execution_errors.append(error)
                    return context
                    
                context.generated_code = "\n".join(code_array)
                print("\033[95m--- Generated Code ---\033[0m")
                print(f"```python\n{context.generated_code}\n```")
                print("\033[95m----------------------\033[0m")
                
                context.current_state = AgentState.EXECUTION
                
        except urllib.error.URLError as e:
            print(f"\033[91m[!] Failed to reach Code Generator API: {e}\033[0m")
            context.current_state = AgentState.ERROR_HANDLING
            context.execution_errors.append(str(e))
            
        return context

class ExecutorAgentInterface(BaseAgentInterface):
    """
    Interface for the Executor Agent (FreeCAD runner).
    """
    def __init__(self, url: str = "http://127.0.0.1:8000/execute"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        print("\n\033[92m[Executor Agent]\033[0m Executing code...")
        
        req_exec = urllib.request.Request(
            self.url,
            data=json.dumps({
                "step_id": context.current_step_index + 1,
                "code": context.generated_code
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req_exec) as response:
                exec_data = json.loads(response.read().decode())
                status = exec_data.get("status")
                
                if status == "SUCCESS":
                    print("\033[92m[+] Code executed successfully!\033[0m")
                    stdout = exec_data.get("stdout", "")
                    if stdout:
                        print(f"\033[90mOutput:\n{stdout}\033[0m")
                        
                    context.runned_codes.append(context.generated_code)
                    context.current_step_index += 1
                    
                    # Check if more steps remain
                    if context.current_step_index < len(context.parameter_steps):
                        context.current_state = AgentState.CODE_GENERATION 
                    else:
                        context.current_state = AgentState.COMPLETED
                else:
                    error_trace = exec_data.get("error_trace", "Unknown Error")
                    print(f"\033[91m[-] Execution Failed!\033[0m")
                    print(f"\033[91mError Trace:\n{error_trace}\033[0m")
                    
                    context.failed_codes.append(context.generated_code)
                    context.execution_errors.append(error_trace)
                    context.current_state = AgentState.ERROR_HANDLING
                    
        except urllib.error.URLError as e:
            print(f"\033[91m[!] Failed to reach Execution API: {e}\033[0m")
            context.execution_errors.append(str(e))
            context.current_state = AgentState.ERROR_HANDLING
            
        return context
