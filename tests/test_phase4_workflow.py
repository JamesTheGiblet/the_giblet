# tests/test_phase4_workflow.py

import pytest
from pathlib import Path
import sys

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) # Ensure core is in path

from core.automator import Automator
from core.utils import write_file, read_file

# --- Evaluation for Task 4.3: Stub Auto-Generator ---

@pytest.fixture
def temp_py_file_for_stubs(tmp_path):
    """Creates a temporary Python file with a mix of complete and incomplete functions."""
    content = """
def fully_implemented_function(a, b):
    # This function is already complete.
    return a + b

def function_with_pass(c, d):
    pass

def function_with_ellipsis(e, f):
    ...

def function_with_docstring_and_pass(g):
    \"\"\"This is a docstring.\"\"\"
    pass

class MyClass:
    def method_with_pass(self):
        pass

    def implemented_method(self):
        print("Hello")
"""
    file_path = tmp_path / "stub_test_file.py"
    # Use the project's own write_file utility for consistency if it's accessible and works,
    # otherwise, use standard pathlib write_text.
    file_path.write_text(content, encoding="utf-8")
    return file_path

def test_automator_stub_generation(temp_py_file_for_stubs, tmp_path, monkeypatch):
    """
    Assesses the automator's ability to correctly add TODO stubs to empty functions.
    """
    automator = Automator()

    # Temporarily set the project's WORKSPACE_DIR to the pytest tmp_path for this test.
    # This allows the utils functions (like read_file) to work within the temp directory
    # without triggering the "outside of workspace" security check.
    monkeypatch.setattr("core.utils.WORKSPACE_DIR", tmp_path)
    
    # Run the stub generation on the test file
    success = automator.generate_stubs(str(temp_py_file_for_stubs))
    assert success, "generate_stubs should return True on success."

    # Read the modified content
    modified_content = read_file(str(temp_py_file_for_stubs))

    # 1. Check that complete functions are untouched
    assert "return a + b" in modified_content, "Existing function bodies should not be changed."
    assert 'print("Hello")' in modified_content, "Existing method bodies should not be changed."

    # 2. Check that stubs were added to empty functions/methods
    expected_stub = "# TODO: Implement this function."
    
    # Split content into lines for easier checking
    lines = modified_content.splitlines()
    
    # Helper to check if a stub exists after a function definition
    def find_stub_after(func_def_line, all_lines):
        try:
            index = all_lines.index(func_def_line)
            # The stub should be on a line following the def, likely indented
            for i in range(index + 1, index + 4): # Check next few lines
                if expected_stub in all_lines[i]:
                    return True
            return False
        except ValueError:
            return False

    assert find_stub_after("def function_with_pass(c, d):", lines), "Stub should be added to function with `pass`."
    assert find_stub_after("def function_with_ellipsis(e, f):", lines), "Stub should be added to function with `...`."
    assert find_stub_after("    def method_with_pass(self):", lines), "Stub should be added to method with `pass`."
    
    # 3. Check that the docstring was preserved
    assert '"""This is a docstring."""' in modified_content
    # The stub should be after the docstring
    docstring_line_index = lines.index('    """This is a docstring."""')
    assert expected_stub in lines[docstring_line_index + 1].strip()
