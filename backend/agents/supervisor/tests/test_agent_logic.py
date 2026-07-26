import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure supervisor package root is on the path when running pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.request import SupervisorRequest
from services.agent_logic import evaluate_complexity


class TestSimplePath:
    def test_make_a_cube(self):
        request = SupervisorRequest(instruction="make a cube", canvas_data=None)
        result = evaluate_complexity(request)
        assert result.routing_path == "simple"
        assert result.matched_primitive == "cube"
        assert result.original_instruction == "make a cube"

    def test_cylinder_with_dimensions(self):
        request = SupervisorRequest(
            instruction="create a cylinder 10mm radius", canvas_data=None
        )
        result = evaluate_complexity(request)
        assert result.routing_path == "simple"
        assert result.matched_primitive == "cylinder"


class TestComplexPath:
    def test_bracket_design(self):
        request = SupervisorRequest(
            instruction="design a bracket with mounting holes", canvas_data=None
        )
        result = evaluate_complexity(request)
        assert result.routing_path == "complex"
        assert result.matched_primitive is None

    def test_sketch_only(self):
        request = SupervisorRequest(
            instruction="", canvas_data={"shapes": []}
        )
        result = evaluate_complexity(request)
        assert result.routing_path == "complex"
        assert result.matched_primitive is None
        assert result.original_instruction == ""


class TestEdgeCases:
    def test_empty_both_inputs_raises(self):
        with pytest.raises(ValidationError):
            SupervisorRequest(instruction="", canvas_data=None)

    def test_empty_instruction_and_empty_canvas_raises(self):
        with pytest.raises(ValidationError):
            SupervisorRequest(instruction="   ", canvas_data={})

    def test_multiple_primitives_first_match_wins(self):
        request = SupervisorRequest(
            instruction="make a cube and a cylinder", canvas_data=None
        )
        result = evaluate_complexity(request)
        assert result.routing_path == "simple"
        assert result.matched_primitive == "cube"

    def test_word_boundary_rejects_toolbox(self):
        request = SupervisorRequest(instruction="open the toolbox", canvas_data=None)
        result = evaluate_complexity(request)
        assert result.routing_path == "complex"
        assert result.matched_primitive is None

    def test_primitive_with_canvas_still_simple(self):
        request = SupervisorRequest(
            instruction="make a sphere",
            canvas_data={"shapes": [{"type": "draw"}]},
        )
        result = evaluate_complexity(request)
        assert result.routing_path == "simple"
        assert result.matched_primitive == "sphere"
