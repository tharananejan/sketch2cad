import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure supervisor package root is on the path when running pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.request import SupervisorRequest
from services.agent_logic import evaluate_complexity


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
        assert result.routing_path == "simple"

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


