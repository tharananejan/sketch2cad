# FreeGen Agent Orchestrator

This directory contains the central state machine router for the FreeGen agents.

## Architecture

The orchestrator uses a pure Python State Machine pattern. It consists of three main components:

1. **Context (`context.py`)**: Defines `OrchestratorContext`, a shared state object that holds all variables (parameters, code, errors) passed between agents.
2. **Interfaces (`agent_interfaces.py`)**: Decoupled wrappers around the actual agents (`ParameterAgent`, `CodeGeneratorAgent`, `ExecutorAgent`). This ensures the core router doesn't break if an agent's internal API changes.
3. **Router (`router.py`)**: The `AgentRouter` runs a `while` loop, checking the current state and calling the respective agent interface until the workflow completes or fails.

## Current Flow

1. **PARAMETER_GATHERING**: The user prompt is analyzed. If a simple shape is found, it interactively asks for missing parameters in the terminal. Generates modeling steps.
2. **CODE_GENERATION**: Sends the steps to the Code Generator SLM.
3. **EXECUTION**: Sends the generated code to the Executor (FreeCAD).
4. **ERROR_HANDLING** *(Placeholder)*: If an error occurs, it will route here.

## How to Scale

To add a new agent (e.g., a Supervisor or Error Handler):
1. Add a new state to `AgentState` in `context.py`.
2. Add any new state variables to `OrchestratorContext`.
3. Create a new interface class in `agent_interfaces.py` that inherits from `BaseAgentInterface`.
4. Register the new interface in the `self.agents` dict inside `router.py`.
