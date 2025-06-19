# tests/test_phase4_workflow.py

import pytest
from pathlib import Path
import sys
import os

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.automator import Automator
from core import utils # Import the whole module to allow monkeypatching

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
    file_path.write_text(content, encoding="utf-8")
    return file_path

def test_automator_stub_generation(temp_py_file_for_stubs, monkeypatch):
    """
    Assesses the automator's ability to correctly add TODO stubs to empty functions.
    """
    # FIX: Temporarily set the project's WORKSPACE to the pytest tmp_path.
    # This allows both automator.generate_stubs (which uses write_file) and the local
    # read_file call to operate within the same sandboxed directory.
    monkeypatch.setattr(utils, 'WORKSPACE_DIR', temp_py_file_for_stubs.parent)
    
    automator = Automator()
    
    # The functions now operate on just the filename, relative to the monkeypatched WORKSPACE_DIR
    file_name = temp_py_file_for_stubs.name
    
    # Run the stub generation on the test file
    success = automator.generate_stubs(file_name)
    assert success, "generate_stubs should return True on success."

    # Read the modified content
    modified_content = utils.read_file(file_name)
    assert modified_content is not None, "read_file should successfully read the modified file."

    # 1. Check that complete functions are untouched
    assert "return a + b" in modified_content, "Existing function bodies should not be changed."
    assert 'print("Hello")' in modified_content, "Existing method bodies should not be changed."

    # 2. Check that stubs were added to empty functions/methods
    expected_stub = "# TODO: Implement this function."
    lines = modified_content.splitlines()
    
    def find_stub_after(func_def_line, all_lines):
        try:
            index = all_lines.index(func_def_line)
            for i in range(index + 1, index + 4):
                if expected_stub in all_lines[i]:
                    return True
            return False
        except (ValueError, IndexError):
            return False

    assert find_stub_after("def function_with_pass(c, d):", lines), "Stub should be added to function with `pass`."
    assert find_stub_after("def function_with_ellipsis(e, f):", lines), "Stub should be added to function with `...`."
    assert find_stub_after("    def method_with_pass(self):", lines), "Stub should be added to method with `pass`."
    
    # 3. Check that the docstring was preserved
    assert '"""This is a docstring."""' in modified_content
    docstring_line_index = lines.index('    """This is a docstring."""')
    assert expected_stub in lines[docstring_line_index + 1].strip()

