# tests/test_phase23_adaptive_generators.py

import pytest
from pathlib import Path
import sys
import json
from unittest.mock import MagicMock, patch

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.readme_generator import ReadmeGenerator
from core.roadmap_generator import RoadmapGenerator
from core.style_preference import StylePreferenceManager
from core.llm_provider_base import LLMProvider
from fastapi.testclient import TestClient

try:
    from api import app
except (ImportError, ModuleNotFoundError):
    pytest.fail("Could not import the FastAPI 'app' from api.py. Please ensure it exists.")

# --- Fixtures ---

@pytest.fixture
def mock_llm_provider():
    """Provides a mocked LLM provider."""
    mock = MagicMock(spec=LLMProvider)
    mock.is_available.return_value = True
    return mock

@pytest.fixture
def temp_style_manager(tmp_path):
    """Provides a StylePreferenceManager using a temporary file."""
    style_file = tmp_path / "test_style.json"
    return StylePreferenceManager(file_path=style_file)

# --- Evaluation for Task 23.1, 23.2, 23.3: Adaptive Generators ---

def test_readme_generator_uses_style_preferences(mock_llm_provider, temp_style_manager):
    """
    Assesses if the ReadmeGenerator incorporates style preferences into its prompt.
    """
    # 1. Set a custom style preference
    temp_style_manager.set_preference("readme.default_tone", "witty")
    
    # 2. Initialize the generator
    readme_gen = ReadmeGenerator(llm_provider=mock_llm_provider, style_manager=temp_style_manager)
    
    project_brief = {"title": "Test Project", "summary": "A test."}
    readme_gen.generate(project_brief)
    
    # 3. Assert that the prompt sent to the LLM contains the custom style
    mock_llm_provider.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm_provider.generate_text.call_args
    # generate_text is called with keyword arguments, so 'prompt' will be in call_kwargs
    assert 'prompt' in call_kwargs, "The 'prompt' keyword argument was not found in the call to generate_text."
    final_prompt = call_kwargs['prompt']
    
    assert "Tone: witty" in final_prompt, "The prompt should reflect the custom 'witty' tone preference."

def test_roadmap_generator_uses_style_preferences(mock_llm_provider, temp_style_manager):
    """
    Assesses if the RoadmapGenerator incorporates style preferences into its prompt.
    """
    # 1. Set a custom style preference
    temp_style_manager.set_preference("roadmap.default_format", "kanban_style")
    
    # 2. Initialize the generator
    roadmap_gen = RoadmapGenerator(llm_provider=mock_llm_provider, style_manager=temp_style_manager)
    
    project_brief = {"title": "Test Project", "summary": "A test."}
    roadmap_gen.generate(project_brief)
    
    # 3. Assert that the prompt sent to the LLM contains the custom style
    mock_llm_provider.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm_provider.generate_text.call_args
    # generate_text is called with keyword arguments, so 'prompt' will be in call_kwargs
    assert 'prompt' in call_kwargs, "The 'prompt' keyword argument was not found in the call to generate_text."
    final_prompt = call_kwargs['prompt']
    
    assert "Roadmap Format: kanban_style" in final_prompt, "The prompt should reflect the custom 'kanban_style' format preference."

def test_reflective_prompts_api_endpoint(temp_style_manager):
    """
    Assesses the API endpoint for updating style preferences.
    """
    # We patch the instance of the style manager used by the API
    with patch('api.style_manager_for_api', temp_style_manager):
        client = TestClient(app)
        
        # 1. Define the style update
        new_readme_settings = {
            "default_style": "minimalist",
            "default_tone": "casual"
        }
        payload = {
            "category": "readme",
            "settings": new_readme_settings
        }
        
        # 2. Call the API endpoint
        response = client.post("/style/set_preferences", json=payload)
        
        # 3. Assert the API call was successful and the preferences were updated
        assert response.status_code == 200, "The API should successfully process the request."
        
        # 4. Verify the changes in our local manager instance (which points to the same file)
        assert temp_style_manager.get_preference("readme.default_style") == "minimalist"
        assert temp_style_manager.get_preference("readme.default_tone") == "casual"
