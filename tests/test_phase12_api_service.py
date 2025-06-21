# tests/test_phase12_api_service.py

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock

from core.llm_provider_base import LLMProvider # Add MagicMock import
# Ensure the api module and its components can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) # Add this line if not already present
try:
    from api import app, memory, idea_synth_for_api, code_generator # Import the instances
except (ImportError, ModuleNotFoundError) as e:
    pytest.fail(f"Could not import the FastAPI 'app' or 'memory' from api.py. Error: {e}")

client = TestClient(app)

# --- Evaluation for Task 12.1, 12.2: API Service Stability ---

@pytest.fixture(autouse=True)
def mock_llm_calls(monkeypatch):
    """
    Automatically mocks the generate_text method for all tests in this file
    to prevent actual LLM calls during API endpoint testing.
    Also mocks is_available to ensure providers appear active.
    """
    # Master mock for generate_text behavior control from tests
    master_mock_generate_text = MagicMock()
    # Default return value, can be overridden in tests
    master_mock_generate_text.return_value = '["mocked plan step 1"]'

    # Create a mock LLM provider instance
    mock_llm_provider_instance = MagicMock(spec=LLMProvider)
    mock_llm_provider_instance.is_available.return_value = True
    mock_llm_provider_instance.generate_text.side_effect = master_mock_generate_text

    # Patch the llm_provider attribute of the actual instances used by the FastAPI app
    monkeypatch.setattr(idea_synth_for_api, "llm_provider", mock_llm_provider_instance)
    monkeypatch.setattr(code_generator, "llm_provider", mock_llm_provider_instance)

    yield master_mock_generate_text # Yield the master mock for configuration and assertions

def test_api_agent_plan_endpoint(mock_llm_calls):
    """
    Assesses the /agent/plan endpoint for stability and correct response structure.
    """
    goal = "Create a simple web server"
    response = client.post("/agent/plan", json={"goal": goal})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "plan" in data, "Response should contain a 'plan' key."
    assert data["plan"] is not None, "The plan should not be null."
    assert isinstance(data["plan"], list), "The plan should be a list."
    
    # Check that the mock was called
    mock_llm_calls.assert_called()

def test_api_file_write_read_endpoints():
    """
    Assesses the file I/O endpoints (/file/write, /file/read) for reliability.
    """
    test_filepath = "test_api_write_file.txt"
    test_content = "This file was written via an API test."
    
    # 1. Test Write Endpoint
    write_response = client.post("/file/write", json={"filepath": test_filepath, "content": test_content})
    assert write_response.status_code == 200
    assert "File updated successfully" in write_response.json().get("message", "")
    
    # 2. Test Read Endpoint
    read_response = client.get(f"/file/read?filepath={test_filepath}")
    assert read_response.status_code == 200
    data = read_response.json()
    assert data.get("content") == test_content
    
    # 3. Clean up the test file
    full_path = Path(__file__).resolve().parent.parent / test_filepath
    if full_path.exists():
        full_path.unlink()

def test_api_generate_function_endpoint(mock_llm_calls):
    """
    Assesses the /generate/function endpoint.
    """
    # The mock will now return a code snippet
    mock_llm_calls.return_value = "def hello_world():\n    print('Hello from API')"
    
    prompt = "a hello world function"
    response = client.post("/generate/function", json={"prompt": prompt})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "generated_code" in data
    assert "def hello_world()" in data["generated_code"]
    mock_llm_calls.assert_called_once()
