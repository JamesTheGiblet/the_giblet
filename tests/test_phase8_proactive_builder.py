# tests/test_phase8_proactive_builder.py

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.code_generator import CodeGenerator
from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile
from core.memory import Memory
from core.project_contextualizer import ProjectContextualizer
from core.style_preference import StylePreferenceManager

# --- Mock Fixtures for Dependencies ---

@pytest.fixture
def mock_builder_dependencies():
    """Provides mocked dependencies for the CodeGenerator used in builder tasks."""
    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.is_available.return_value = True
    mock_llm.model_name = "mock-builder-model"
    
    mock_user_profile = MagicMock(spec=UserProfile)
    # Set up mock return values for any preferences the generator might use
    mock_user_profile.get_preference.return_value = 'default' 
    
    # The CodeGenerator now requires a StylePreferenceManager
    mock_style_manager = MagicMock(spec=StylePreferenceManager)

    return {
        "user_profile": mock_user_profile,
        "memory_system": MagicMock(spec=Memory),
        "llm_provider": mock_llm,
        "project_contextualizer": MagicMock(spec=ProjectContextualizer),
        "style_preference_manager": mock_style_manager
    }

# --- Evaluation for Task 8.1, 8.2, 8.3: Proactive Builder Engine ---

def test_code_generator_function_generation_prompt(mock_builder_dependencies):
    """
    Assesses that the prompt for standard function generation is correctly formed.
    """
    code_gen = CodeGenerator(**mock_builder_dependencies)
    mock_llm = mock_builder_dependencies["llm_provider"]
    mock_llm.generate_text.return_value = "def my_func(): pass"
    
    user_prompt = "a function that adds two numbers"
    code_gen.generate_function(user_prompt)
    
    mock_llm.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm.generate_text.call_args
    final_prompt = call_kwargs.get('prompt', call_args[0])
    
    assert user_prompt in final_prompt, "The user's original prompt should be in the final prompt."
    assert "generate a Python function" in final_prompt.lower(), "The prompt should instruct the LLM to generate a function."

def test_code_generator_refactor_prompt(mock_builder_dependencies):
    """
    Assesses that the prompt for refactoring includes both the source code and the instruction.
    """
    code_gen = CodeGenerator(**mock_builder_dependencies)
    mock_llm = mock_builder_dependencies["llm_provider"]
    mock_llm.generate_text.return_value = "# refactored code"

    source_code = "def F(n): return 1 if n < 2 else F(n-1)+F(n-2)"
    instruction = "make this more efficient"
    
    code_gen.refactor_code(source_code, instruction)
    
    mock_llm.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm.generate_text.call_args
    final_prompt = call_kwargs.get('prompt', call_args[0])

    assert source_code in final_prompt, "The refactor prompt must include the original source code."
    assert instruction in final_prompt, "The refactor prompt must include the user's instruction."
    assert "refactor the following python code" in final_prompt.lower(), "The prompt's instructions are incorrect."

def test_code_generator_ui_build_prompt(mock_builder_dependencies):
    """
    Assesses that the prompt for UI generation includes the data model.
    """
    code_gen = CodeGenerator(**mock_builder_dependencies)
    mock_llm = mock_builder_dependencies["llm_provider"]
    mock_llm.generate_text.return_value = "# streamlit ui code"

    data_model_code = "class Person:\n  name: str\n  age: int"
    file_path = "person_model.py"

    code_gen.generate_streamlit_ui(data_model_code, file_path)
    
    mock_llm.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm.generate_text.call_args
    final_prompt = call_kwargs.get('prompt', call_args[0])
    
    assert data_model_code in final_prompt, "The UI generation prompt must include the data model source code."
    assert file_path in final_prompt, "The UI generation prompt should mention the source file path."
    assert "streamlit" in final_prompt.lower(), "The prompt must instruct the LLM to use Streamlit."

