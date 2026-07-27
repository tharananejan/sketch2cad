"""
Verification test script for Code Generator Agent components.
"""

import sys
import os
import unittest

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deps import get_settings
from tools.error_parser import extract_python_code, validate_python_syntax
from services.rag_retriever import chunk_text, retrieve_context
from services.agent_logic import _load_system_prompt


class TestCodeGeneratorComponents(unittest.TestCase):
    def test_settings(self):
        settings = get_settings()
        self.assertEqual(settings.LLM_MODEL, "qwen2.5-coder:0.5b")
        self.assertTrue(os.path.exists(settings.KNOWLEDGE_DIR))
        self.assertTrue(os.path.exists(settings.CHROMA_PERSIST_DIR))

    def test_error_parser_extraction(self):
        raw_llm_output = (
            "Here is your FreeCAD code:\n\n"
            "```python\n"
            "import FreeCAD as App\n"
            "import Part\n"
            "doc = App.ActiveDocument\n"
            "box = doc.addObject('Part::Box', 'Box')\n"
            "doc.recompute()\n"
            "```\n\n"
            "Hope this helps!"
        )
        cleaned = extract_python_code(raw_llm_output)
        self.assertIn("import FreeCAD as App", cleaned)
        self.assertNotIn("Here is your FreeCAD code", cleaned)
        self.assertNotIn("```", cleaned)

    def test_error_parser_validation(self):
        valid_code = "import FreeCAD\nprint('Hello World')"
        is_valid, err = validate_python_syntax(valid_code)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

        invalid_code = "import FreeCAD\nprint('unclosed string)"
        is_valid, err = validate_python_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(err)

    def test_chunking(self):
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = chunk_text(text, chunk_size=30, overlap=5)
        self.assertGreater(len(chunks), 1)

    def test_system_prompt_loading(self):
        settings = get_settings()
        prompt = _load_system_prompt(settings)
        self.assertIn("FreeCAD", prompt)
        self.assertIn("step not available", prompt)

    def test_step_not_available_handling(self):
        raw_output = "I don't have instructions for this. step not available"
        extracted = extract_python_code(raw_output)
        self.assertEqual(extracted, "step not available")
        is_valid, err = validate_python_syntax(extracted)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_request_schema_flexibility(self):
        from schemas.request import CodeGenerateRequest
        req1 = CodeGenerateRequest.model_validate({"step": "make a cube (5mm,5mm,10mm)"})
        self.assertEqual(req1.step, "make a cube (5mm,5mm,10mm)")
        req2 = CodeGenerateRequest.model_validate({"instruction": "make a cyclinder(10,10,10)"})
        self.assertEqual(req2.step, "make a cyclinder(10,10,10)")

    def test_response_schema_error_field(self):
        from schemas.response import CodeGenerateResponse
        resp = CodeGenerateResponse(code="step not available", error="step not available")
        self.assertEqual(resp.error, "step not available")


if __name__ == "__main__":
    unittest.main()
