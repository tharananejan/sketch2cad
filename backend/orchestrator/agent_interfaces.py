import sys
import os
import urllib.request
import urllib.error
import json
from typing import Optional

from .context import OrchestratorContext, AgentState

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
                    print(f"\n\033[96m🤖 Parameter Agent Asks:\033[0m \033[93m{question}\033[0m")
                    
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
    """
    def __init__(self, url: str = "http://127.0.0.1:8004/planner"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        print(f"\n\033[95m[Planner Agent]\033[0m Planning steps for: '{context.user_prompt}'...")
        
        # We need a loop here just like the parameter agent because the planner
        # can ask for missing parameters for complex shapes.
        
        # Dictionary to store answers to planner's questions
        # Note: In the future, this could be stored on the OrchestratorContext
        # but for now we keep it localized to this planning session.
        parameter_answers = {}
        
        while True:
            payload = {
                "request": context.user_prompt,
                "context": {
                    "parameter_answers": parameter_answers,
                    # We send empty lists for these as they are used for iterative replanning (not implemented yet)
                    "completed_steps": [],
                    "remaining_steps": [],
                    "errors": [],
                    "pending_questions": [] 
                }
            }
            
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
                        questions = res_data.get("questions", [])
                        for q in questions:
                            q_id = q.get("parameter_id")
                            q_text = q.get("question")
                            reason = q.get("reason", "")
                            
                            # Skip if we already answered it
                            if q_id in parameter_answers:
                                continue
                                
                            print(f"\n\033[96m🤖 Planner Agent Asks:\033[0m \033[93m{q_text}\033[0m")
                            if reason:
                                print(f"\033[90m({reason})\033[0m")
                                
                            try:
                                user_answer = input("\033[92mYour Answer > \033[0m").strip()
                            except (EOFError, KeyboardInterrupt):
                                print("\n\033[91m[!] Input interrupted. Aborting.\033[0m")
                                context.current_state = AgentState.FAILED
                                return context
                                
                            if user_answer:
                                # Send raw string to the planner, let it parse it or we could format it
                                parameter_answers[q_id] = user_answer
                                
                        # Loop again to send answers
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
                        for i, step in enumerate(flat_steps):
                            # Pass just the description/title to Code Generator
                            step_text = step.get("description", step.get("title", ""))
                            print(f"  {i+1}. {step_text}")
                            context.parameter_steps.append(step_text)
                            
                        context.current_state = AgentState.CODE_GENERATION
                        return context
                        
                    else:
                        print(f"\033[91m[!] Unknown Planner Status: {status}\033[0m")
                        context.current_state = AgentState.ERROR_HANDLING
                        return context
                        
            except urllib.error.URLError as e:
                print(f"\033[91m[!] Failed to reach Planner API: {e}\033[0m")
                context.execution_errors.append(str(e))
                context.current_state = AgentState.ERROR_HANDLING
                return context

class CodeGeneratorAgentInterface(BaseAgentInterface):
    """
    Interface for the lightweight SLM Code Generator Agent.
    """
    def __init__(self, url: str = "http://127.0.0.1:8001/generate"):
        self.url = url

    def process(self, context: OrchestratorContext) -> OrchestratorContext:
        if context.current_step_index >= len(context.parameter_steps):
            context.current_state = AgentState.COMPLETED
            return context
            
        step = context.parameter_steps[context.current_step_index]
        print(f"\n\033[95m[Code Generator Agent]\033[0m Generating code for step: '{step}'...")
        
        req_gen = urllib.request.Request(
            self.url,
            data=json.dumps({"step": step}).encode("utf-8"),
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
                print(context.generated_code)
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
