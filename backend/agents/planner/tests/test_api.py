from __future__ import annotations

import json

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from backend.agents.planner.api import app
from backend.agents.planner.dependencies import get_planner_service
from backend.agents.planner.service import PlannerService
from backend.agents.planner.tests.test_service import FakeProvider


def test_root_returns_planner_ui() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Sketch2CAD Frontier Planner" in response.text
    assert 'fetch("/planner"' in response.text


def test_endpoint_returns_only_the_plan_response_shape() -> None:
    response_text = json.dumps(
        {
            "status": "planned",
            "steps": [
                {
                    "step_id": 1,
                    "title": "Establish base geometry",
                    "description": "Create the base geometry for the requested enclosure.",
                    "depends_on": [],
                }
            ],
        }
    )
    app.dependency_overrides[get_planner_service] = lambda: PlannerService(FakeProvider(response_text))

    try:
        client = TestClient(app)
        response = client.post("/planner", json={"request": "Design a compact enclosure."})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert set(response.json()) == {"status", "plan_id", "complexity", "steps"}
    assert response.json()["status"] == "planned"
    assert response.json()["complexity"] == "complex"


def test_endpoint_returns_needs_parameters_response_shape() -> None:
    response_text = json.dumps(
        {
            "status": "needs_parameters",
            "questions": [
                {
                    "parameter_id": "side_length",
                    "question": "What side length should the cube have?",
                    "value_type": "number",
                    "unit": "mm",
                    "options": [],
                    "reason": "A cube requires one equal side length.",
                }
            ],
        }
    )
    app.dependency_overrides[get_planner_service] = lambda: PlannerService(FakeProvider(response_text))

    try:
        client = TestClient(app)
        response = client.post("/planner", json={"request": "Generate a cube."})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert set(response.json()) == {"status", "plan_id", "complexity", "questions"}
    assert response.json()["status"] == "needs_parameters"
    assert response.json()["questions"][0]["parameter_id"] == "side_length"


def test_endpoint_returns_json_error_envelope_for_empty_request() -> None:
    app.dependency_overrides[get_planner_service] = lambda: PlannerService(FakeProvider("{}"))

    try:
        client = TestClient(app)
        response = client.post("/planner", json={"request": ""})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_endpoint_returns_json_error_envelope_for_missing_provider_config(
    monkeypatch: MonkeyPatch,
) -> None:
    app.dependency_overrides.clear()
    get_planner_service.cache_clear()
    monkeypatch.setattr("backend.agents.planner.config.load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.delenv("PLANNER_PROVIDER", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    try:
        client = TestClient(app)
        response = client.post("/planner", json={"request": "Design a hinged bracket assembly."})
    finally:
        get_planner_service.cache_clear()

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "planner_configuration_error",
            "message": "GROQ_API_KEY must be configured.",
            "details": {"setting": "GROQ_API_KEY"},
        }
    }
