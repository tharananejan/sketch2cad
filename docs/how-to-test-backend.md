# How to Test the FreeGen Backend

This document outlines the testing strategies, unit tests, and steps to run and verify the FreeGen backend services and agent APIs.

---

## 1. Environment Setup

Ensure environment variables are configured in `.env` at the project root directory (refer to [ENV_KEYS.md](../ENV_KEYS.md) for required keys such as `GROQ_API_KEY_SUPERVISOR`, `DEEPSEEK_API_KEY_PLANNER`, etc.).

Make sure Python dependencies and `pytest` are installed:
```bash
pip install pytest uvicorn fastapi requests
```

---

## 2. Running Automated Unit Tests

FreeGen contains unit test suites distributed across its agent microservices. You can execute tests using `pytest`.

### Run All Backend Tests
To run all backend tests from the workspace root:
```bash
pytest backend/
```

### Run Tests for Specific Agents
- **Supervisor Agent:**
  ```bash
  pytest backend/agents/supervisor/tests/
  ```
- **Planner Agent:**
  ```bash
  pytest backend/agents/planner/tests/
  ```
- **Code Generator Agent:**
  ```bash
  pytest backend/agents/code-generator/
  ```
- **Code Executor:**
  ```bash
  pytest backend/agents/execution/
  ```

---

## 3. End-to-End & Interactive Testing

To test the multi-agent system interactively:

1. **Start the Backend Services and Orchestrator:**
   Run the master backend script:
   ```bash
   python backend/run.py
   ```
   This will spin up all 5 microservice APIs (ports 8000–8004):
   - **Execution Agent API** (`http://127.0.0.1:8000`)
   - **Code Generator API** (`http://127.0.0.1:8001`)
   - **Parameter API** (`http://127.0.0.1:8002`)
   - **Supervisor API** (`http://127.0.0.1:8003`)
   - **Planner API** (`http://127.0.0.1:8004`)

2. **Send CAD Instructions:**
   Once the prompt `CAD Instruction >` appears in your terminal, enter a test prompt, such as:
   ```text
   Create a parametric cylinder with height 50mm and radius 15mm
   ```

3. **Verify Execution Output:**
   Observe the orchestrator logs as the request moves through:
   `COMPLEXITY_CHECK` → `PARAMETER_GATHERING` → `PLANNING` → `CODE_GENERATION` → `EXECUTION`
