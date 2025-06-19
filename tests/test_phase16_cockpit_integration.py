# tests/test_phase16_cockpit_integration.py

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock # Import MagicMock
import os

# Ensure the api module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from api import app
    from core import utils
except (ImportError, ModuleNotFoundError) as e:
    pytest.fail(f"Could not import the FastAPI 'app' or 'utils' from the project. Error: {e}")

client = TestClient(app)

# --- Fixture to mock LLM calls ---

@pytest.fixture(autouse=True)
def mock_llm_calls():
    """Mocks the LLM provider to avoid actual API calls during tests."""
    # Master mock for generate_text behavior control from tests
    master_mock_generate_text = MagicMock()
    # Default return value, can be overridden in tests
    master_mock_generate_text.return_value = '{"mock": "response"}'

    def side_effect_for_provider_generate_text(*args, **kwargs):
        return master_mock_generate_text(*args, **kwargs)

    with patch('core.llm_providers.GeminiProvider.generate_text', side_effect=side_effect_for_provider_generate_text) as mock_gemini_gen, \
         patch('core.llm_providers.OllamaProvider.generate_text', side_effect=side_effect_for_provider_generate_text) as mock_ollama_gen, \
         patch('core.llm_providers.GeminiProvider.is_available', return_value=True) as mock_gemini_available, \
         patch('core.llm_providers.OllamaProvider.is_available', return_value=True) as mock_ollama_available:
        
        # Yield the master mock so tests can configure its return_value and assert calls
        yield master_mock_generate_text

# --- Evaluation for Task 16.1, 16.2, 16.3, 16.4: Interactive Cockpit ---

def test_cockpit_generator_endpoint(mock_llm_calls):
    """
    Assesses the /generate/function endpoint for the 'Generator' tab.
    """
    mock_llm_calls.return_value = "def generated_func(): pass"
    response = client.post("/generate/function", json={"prompt": "a test function"})
    
    assert response.status_code == 200, "Generator endpoint should return 200 OK."
    data = response.json()
    assert "generated_code" in data, "Response should contain generated_code."
    assert "def generated_func()" in data["generated_code"]

def test_cockpit_refactor_endpoint(mock_llm_calls, tmp_path):
    """
    Assesses the /refactor endpoint for the 'Refactor' tab.
    """
    # Setup a temporary file within a temporary workspace
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(utils, 'WORKSPACE_DIR', tmp_path)
    
    test_file = tmp_path / "refactor_test_file.py"
    original_code = "def old_func(): return 1"
    test_file.write_text(original_code)
    
    mock_llm_calls.return_value = "def new_func(): return 2"
    
    response = client.post("/refactor", json={
        "filepath": str(test_file.relative_to(tmp_path)), 
        "instruction": "rename function"
    })

    assert response.status_code == 200, "Refactor endpoint should return 200 OK."
    data = response.json()
    assert data.get("original_code") == original_code
    assert data.get("refactored_code") == "def new_func(): return 2"

def test_cockpit_file_explorer_endpoints(tmp_path):
    """
    Assesses the /files/list and /file/read endpoints for the 'File Explorer' tab.
    """
    # Setup a temporary file
    test_file = tmp_path / "explorer_test.txt"
    test_content = "File explorer test content"
    test_file.write_text(test_content)
    
    # Patch the workspace to our temporary directory
    with patch('core.utils.WORKSPACE_DIR', tmp_path):
        # Test /files/list
        list_response = client.get("/files/list")
        assert list_response.status_code == 200
        assert "explorer_test.txt" in list_response.json().get("files", [])

        # Test /file/read
        read_response = client.get(f"/file/read?filepath=explorer_test.txt")
        assert read_response.status_code == 200
        assert read_response.json().get("content") == test_content

def test_cockpit_automation_changelog_endpoint():
    """
    Assesses the /automate/changelog endpoint for the 'Automation' tab.
    This test uses a mock of git.Repo to avoid needing a real git repository.
    """
    with patch('core.automator.git.Repo') as mock_repo:
        # Configure the mock repo and its commits
        mock_commit = MagicMock()
        mock_commit.message = "feat: Test automation endpoint"
        mock_commit.hexsha = "abcdef1"
        mock_commit.author.name = "Test User"
        mock_commit.committed_date = 1672531200 # 2023-01-01

        mock_active_branch = MagicMock()
        mock_active_branch.name = "test-branch"
        
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.iter_commits.return_value = [mock_commit]
        mock_repo_instance.active_branch = mock_active_branch
        
        response = client.post("/automate/changelog")
        
        assert response.status_code == 200, "Changelog endpoint should return 200 OK."
        assert "Changelog generated successfully" in response.json().get("message", "")

        # Cleanup the created changelog file
        changelog_dir = utils.WORKSPACE_DIR / "data" / "changelogs"
        for f in changelog_dir.glob("CHANGELOG_test-branch_*.md"):
            os.remove(f)
