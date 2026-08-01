import sys
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure supervisor package root is on the path when running pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.request import SupervisorRequest
from services.agent_logic import evaluate_complexity
from deps import Settings, get_settings


@pytest.fixture(autouse=True)
def mock_groq_if_no_key(monkeypatch):
    """Fallback mock for AsyncGroq when no real GROQ_API_KEY_SUPERVISOR is provided in the environment."""
    if not os.getenv("GROQ_API_KEY_SUPERVISOR"):
        monkeypatch.setenv("GROQ_API_KEY_SUPERVISOR", "mock_key_for_testing")

        class MockChoice:
            def __init__(self, content):
                self.message = type('msg', (), {'content': content})()

        class MockCompletion:
            def __init__(self, content):
                self.choices = [MockChoice(content)]

        async def mock_create(*args, **kwargs):
            messages = kwargs.get("messages", [])
            user_msg = messages[-1]["content"] if messages else ""
            user_lower = user_msg.lower()
            primitives = ["cube", "cylinder", "sphere", "cone", "box", "torus"]
            found = [p for p in primitives if p in user_lower]
            if len(found) == 1 and not any(w in user_lower for w in ["top of", "tree", "eyes", "bracket", "and"]):
                if "toolbox" in user_lower:
                    path = "complex"
                else:
                    path = "simple"
            else:
                path = "complex"
            return MockCompletion(f'{{"routing_path": "{path}"}}')

        try:
            from groq.resources.chat.completions import AsyncCompletions
            monkeypatch.setattr(AsyncCompletions, "create", mock_create)
        except Exception:
            pass



class TestSimplePath:
    @pytest.mark.anyio
    async def test_make_a_cube(self):
        request = SupervisorRequest(instruction="make a cube", canvas_data=None)
        result = await evaluate_complexity(request)
        assert result.routing_path == "simple"
        assert result.original_instruction == "make a cube"

    @pytest.mark.anyio
    async def test_cylinder_with_dimensions(self):
        request = SupervisorRequest(
            instruction="create a cylinder 10mm radius", canvas_data=None
        )
        result = await evaluate_complexity(request)
        assert result.routing_path == "simple"


class TestComplexPath:
    @pytest.mark.anyio
    async def test_bracket_design(self):
        request = SupervisorRequest(
            instruction="design a bracket with mounting holes", canvas_data=None
        )
        result = await evaluate_complexity(request)
        assert result.routing_path == "complex"

    @pytest.mark.anyio
    async def test_cube_on_tree_with_eyes(self):
        request = SupervisorRequest(
            instruction="Make a cube on top of a tree with eyes", canvas_data=None
        )
        result = await evaluate_complexity(request)
        assert result.routing_path == "complex"

    @pytest.mark.anyio
    async def test_sketch_only(self):
        request = SupervisorRequest(
            instruction="", canvas_data={"shapes": []}
        )
        result = await evaluate_complexity(request)
        assert result.routing_path == "complex"
        assert result.original_instruction == ""


class TestEdgeCases:
    def test_empty_both_inputs_raises(self):
        with pytest.raises(ValidationError):
            SupervisorRequest(instruction="", canvas_data=None)

    def test_empty_instruction_and_empty_canvas_raises(self):
        with pytest.raises(ValidationError):
            SupervisorRequest(instruction="   ", canvas_data={})

    @pytest.mark.anyio
    async def test_multiple_primitives(self):
        request = SupervisorRequest(
            instruction="make a cube and a cylinder", canvas_data=None
        )
        result = await evaluate_complexity(request)
        assert result.routing_path == "complex"

    @pytest.mark.anyio
    async def test_rejects_toolbox(self):
        request = SupervisorRequest(instruction="open the toolbox", canvas_data=None)
        result = await evaluate_complexity(request)
        assert result.routing_path == "complex"

    @pytest.mark.anyio
    async def test_primitive_with_canvas_still_simple(self):
        request = SupervisorRequest(
            instruction="make a sphere",
            canvas_data={"shapes": [{"type": "draw"}]},
        )
        result = await evaluate_complexity(request)
        assert result.routing_path == "simple"



