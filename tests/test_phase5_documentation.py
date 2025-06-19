# tests/test_phase5_documentation.py

import pytest
from pathlib import Path
import sys
import os
import git
from unittest.mock import MagicMock, patch

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.automator import Automator
from core.code_generator import CodeGenerator
from core import utils
from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile
from core.memory import Memory
from core.project_contextualizer import ProjectContextualizer
from core.style_preference import StylePreferenceManager

# --- Evaluation for Task 5.3: Autogenerate Changelog ---

@pytest.fixture
def temp_git_repo(tmp_path, monkeypatch):
    """
    Creates a temporary Git repository and sets the project's WORKSPACE_DIR to it
    for the duration of the test.
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    repo = git.Repo.init(repo_path)
    
    # Create and commit some files
    (repo_path / "file1.txt").write_text("Initial content")
    repo.index.add(["file1.txt"])
    repo.index.commit("feat: Add initial file")

    (repo_path / "file2.py").write_text("print('Hello')")
    repo.index.add(["file2.py"])
    repo.index.commit("fix: Add hello world script")
    
    # FIX: Patch the WORKSPACE_DIR in the utils module to point to our temp repo
    # This ensures that any part of the app that uses utils.WORKSPACE_DIR will
    # operate within our temporary test environment.
    monkeypatch.setattr(utils, 'WORKSPACE_DIR', repo_path)
    yield repo_path


def test_automator_changelog_generation(temp_git_repo):
    """
    Assesses the automator's ability to generate a changelog from Git history.
    """
    # This now assumes that the Automator uses utils.WORKSPACE_DIR to find the repo
    # and to determine where to write the changelog.
    automator = Automator()
    
    # The changelog should now be created relative to the monkeypatched WORKSPACE_DIR.
    changelog_dir = temp_git_repo / "data" / "changelogs"
    
    success = automator.generate_changelog()
    assert success, "generate_changelog should return True on success."
    
    # Find the created changelog file within the temporary directory
    created_files = list(changelog_dir.glob("*.md"))
    assert len(created_files) > 0, "A changelog file should have been created in the temp directory."
    
    changelog_content = created_files[0].read_text()

    assert "feat: Add initial file" in changelog_content, "Changelog should contain the first commit message."
    assert "fix: Add hello world script" in changelog_content, "Changelog should contain the second commit message."


# --- Evaluation for Task 5.1 & 10.1: Unit Test Generation ---

@pytest.fixture
def mock_code_gen_dependencies():
    """Provides mocked dependencies for the CodeGenerator."""
    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.is_available.return_value = True
    mock_llm.model_name = "mock-test-model" # For LLMCapabilities
    
    mock_user_profile = MagicMock(spec=UserProfile)
    mock_user_profile.get_preference.return_value = 'default_persona'

    return {
        "user_profile": mock_user_profile,
        "memory_system": MagicMock(spec=Memory),
        "llm_provider": mock_llm,
        "project_contextualizer": MagicMock(spec=ProjectContextualizer),
        # FIX: The CodeGenerator now requires a style_manager in its __init__
        "style_preference_manager": MagicMock(spec=StylePreferenceManager)
    }

def test_code_generator_unit_test_prompting(mock_code_gen_dependencies):
    """
    Assesses that the CodeGenerator prepares the correct prompt for unit test generation.
    """
    # FIX: The 'with patch(...)' was incorrect and unnecessary.
    # We pass the mocked style manager in the dependencies fixture instead.
    code_gen = CodeGenerator(**mock_code_gen_dependencies)
    
    source_code = "def add(a, b):\n    return a + b"
    file_path = "my_math_lib.py"
    
    mock_llm = mock_code_gen_dependencies["llm_provider"]
    mock_llm.generate_text.return_value = "# Pytest code here"

    code_gen.generate_unit_tests(source_code, file_path)

    mock_llm.generate_text.assert_called_once()
    
    call_args, call_kwargs = mock_llm.generate_text.call_args
    prompt = call_kwargs.get('prompt')
    if prompt is None and call_args:
        prompt = call_args[0]

    assert prompt is not None, "Prompt should not be None when calling the LLM."
    assert source_code in prompt, "The prompt must contain the source code to be tested."
    assert "pytest" in prompt.lower(), "The prompt should mention pytest."
    assert file_path in prompt, "The prompt should include the file path for context."
    assert "generate a comprehensive suite of unit tests" in prompt, "The prompt's instructions are incorrect."

