from typing import Dict
from .context import OrchestratorContext, AgentState
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
    def __init__(self):
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

    def run(self, initial_prompt: str) -> OrchestratorContext:
        print(f"\n\033[1m\033[96m[Orchestrator] Starting workflow for:\033[0m '{initial_prompt}'")
        
        context = OrchestratorContext(user_prompt=initial_prompt)
        context.planner_parameters = self.persistent_parameters.copy()
        context.session_completed_steps = self.session_completed_steps.copy()
        
        while True:
            current = context.current_state
            
            if current == AgentState.COMPLETED:
                print("\n\033[1m\033[92m[Orchestrator] Workflow Completed Successfully.\033[0m")
                # Save successful execution state for future commands
                self.persistent_parameters.update(context.planner_parameters)
                if context.parameter_steps:
                    self.session_completed_steps.extend(context.parameter_steps)
                break
                
            if current == AgentState.FAILED:
                print("\n\033[1m\033[91m[Orchestrator] Workflow Failed.\033[0m")
                break
                
            if current == AgentState.ERROR_HANDLING:
                # We haven't implemented ErrorHandlingAgent yet, so we just fail for now.
                print("\n\033[93m[Orchestrator] Error Handling triggered, but agent not connected yet. Failing.\033[0m")
                context.current_state = AgentState.FAILED
                continue

            agent = self.agents.get(current)
            if not agent:
                print(f"\n\033[91m[Orchestrator] No agent registered for state {current}. Failing.\033[0m")
                context.current_state = AgentState.FAILED
                continue
                
            try:
                # Agent processes context and returns updated context (including new state)
                context = agent.process(context)
            except Exception as e:
                print(f"\n\033[91m[Orchestrator] Unexpected error in {current}: {e}\033[0m")
                context.current_state = AgentState.FAILED
                
        return context
