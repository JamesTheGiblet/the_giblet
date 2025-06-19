# tests/test_phase12_api_service.py

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock # Add MagicMock import
# Ensure the api module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from api import app, memory
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

    def side_effect_for_provider_generate_text(*args, **kwargs):
        return master_mock_generate_text(*args, **kwargs)

    with patch('core.llm_providers.GeminiProvider.generate_text', side_effect=side_effect_for_provider_generate_text) as mock_gemini_gen, \
         patch('core.llm_providers.OllamaProvider.generate_text', side_effect=side_effect_for_provider_generate_text) as mock_ollama_gen, \
         patch('core.llm_providers.GeminiProvider.is_available', return_value=True) as mock_gemini_available, \
         patch('core.llm_providers.OllamaProvider.is_available', return_value=True) as mock_ollama_available:
        
        # Yield the master mock so tests can configure its return_value and assert calls
        yield master_mock_generate_text

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
