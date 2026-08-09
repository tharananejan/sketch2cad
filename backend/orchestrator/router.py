from typing import Any, Dict
from .context import OrchestratorContext, AgentState
from .error_logger import log_error
from .agent_interfaces import (
    BaseAgentInterface,
    SupervisorAgentInterface,
    PlannerAgentInterface,
    ParameterAgentInterface,
    CodeGeneratorAgentInterface,
    ExecutorAgentInterface
)

class AgentRouter:
    """
    Main state machine orchestrator.
    Routes the execution context to the appropriate agent based on current_state.
    """
    def __init__(self, status_callback=None):
        # Register the agents
        self.agents: Dict[AgentState, BaseAgentInterface] = {
            AgentState.COMPLEXITY_CHECK: SupervisorAgentInterface(),
            AgentState.PLANNING: PlannerAgentInterface(),
            AgentState.PARAMETER_GATHERING: ParameterAgentInterface(),
            AgentState.CODE_GENERATION: CodeGeneratorAgentInterface(),
            AgentState.EXECUTION: ExecutorAgentInterface(),
            # Placeholder for future error handling agent
            AgentState.ERROR_HANDLING: None 
        }
        self.persistent_parameters: Dict[str, Any] = {}
        self.session_completed_steps: list[str] = []
        self.status_callback = status_callback

    def _notify(self, state: str, message: str = None):
        if self.status_callback:
            self.status_callback({"state": state, "message": message})

    def run(self, initial_prompt: str) -> OrchestratorContext:
        print(f"\n\033[1m\033[96m[Orchestrator] Starting workflow for:\033[0m '{initial_prompt}'")
        self._notify("STARTED", initial_prompt)
        
        context = OrchestratorContext(user_prompt=initial_prompt)
        context.planner_parameters = self.persistent_parameters.copy()
        context.session_completed_steps = self.session_completed_steps.copy()
        
        while True:
            current = context.current_state
            self._notify(current.value if hasattr(current, 'value') else str(current))
            
            if current == AgentState.COMPLETED:
                print("\n\033[1m\033[92m[Orchestrator] Workflow Completed Successfully.\033[0m")
                self._notify("COMPLETED", "Workflow Completed Successfully.")
                # Save successful execution state for future commands
                self.persistent_parameters.update(context.planner_parameters)
                if context.parameter_steps:
                    self.session_completed_steps.extend(context.parameter_steps)
                break
                
            if current == AgentState.FAILED:
                print("\n\033[1m\033[91m[Orchestrator] Workflow Failed.\033[0m")
                self._notify("FAILED", "Workflow Failed.")
                # Log error for future error-handling agent development
                error_msg = "; ".join(context.execution_errors) if context.execution_errors else "Unknown failure"
                log_error(
                    agent_state="FAILED",
                    user_prompt=context.user_prompt,
                    error_message=error_msg,
                    generated_code=context.generated_code or None,
                )
                break
                
            if current == AgentState.ERROR_HANDLING:
                # We haven't implemented ErrorHandlingAgent yet, so we just fail for now.
                print("\n\033[93m[Orchestrator] Error Handling triggered, but agent not connected yet. Failing.\033[0m")
                self._notify("FAILED", "Error Handling triggered, but agent not connected yet.")
                # Log error for future error-handling agent development
                error_msg = "; ".join(context.execution_errors) if context.execution_errors else "Error handling triggered"
                log_error(
                    agent_state="ERROR_HANDLING",
                    user_prompt=context.user_prompt,
                    error_message=error_msg,
                    generated_code=context.generated_code or None,
                )
                context.current_state = AgentState.FAILED
                continue

            agent = self.agents.get(current)
            if not agent:
                print(f"\n\033[91m[Orchestrator] No agent registered for state {current}. Failing.\033[0m")
                self._notify("FAILED", f"No agent registered for state {current}.")
                context.current_state = AgentState.FAILED
                continue
                
            try:
                # Agent processes context and returns updated context (including new state)
                context = agent.process(context)
            except Exception as e:
                print(f"\n\033[91m[Orchestrator] Unexpected error in {current}: {e}\033[0m")
                self._notify("FAILED", f"Unexpected error in {current}: {e}")
                log_error(
                    agent_state=str(current),
                    user_prompt=context.user_prompt,
                    error_message=f"Unexpected exception: {e}",
                    generated_code=context.generated_code or None,
                )
                context.current_state = AgentState.FAILED
                
        return context
