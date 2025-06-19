# tests/test_phase19_llm_connector.py

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import json

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.llm_provider_base import LLMProvider
from core.llm_providers import GeminiProvider, OllamaProvider
from core.user_profile import UserProfile
from core.memory import Memory
from core.llm_capabilities import LLMCapabilities
from core.capability_assessor import CapabilityAssessor
from core.code_generator import CodeGenerator
from core.idea_synth import IdeaSynthesizer
from core.style_preference import StylePreferenceManager
from core.project_contextualizer import ProjectContextualizer

# A helper function similar to the one in cli.py/api.py for testing provider selection
def get_llm_provider_from_profile(profile: UserProfile) -> LLMProvider:
    provider_name = profile.get_preference("llm_provider_config", "active_provider", "gemini")
    provider_configs = profile.get_preference("llm_provider_config", "providers", {})
    
    if provider_name == "ollama":
        config = provider_configs.get("ollama", {})
        return OllamaProvider(model_name=config.get("model_name"), base_url=config.get("base_url"))
    # Default to Gemini
    config = provider_configs.get("gemini", {})
    return GeminiProvider(model_name=config.get("model_name"), api_key=config.get("api_key"))

# --- Evaluation for Task 19.1 & 19.2: Provider Selection ---

def test_dynamic_llm_provider_selection(tmp_path):
    """
    Assesses if the provider selection logic correctly interprets the UserProfile.
    """
    profile = UserProfile(memory_system=Memory(file_path=tmp_path / "mem.json"), file_path=tmp_path / "prof.json")
    
    # 1. Test with Ollama configured
    profile.add_preference("llm_provider_config", "active_provider", "ollama")
    profile.add_preference("llm_provider_config.providers.ollama", "model_name", "test-ollama-model")
    
    provider = get_llm_provider_from_profile(profile)
    assert isinstance(provider, OllamaProvider), "Should select OllamaProvider based on profile."
    assert provider.model_name == "test-ollama-model"
    
    # 2. Test with Gemini configured
    profile.add_preference("llm_provider_config", "active_provider", "gemini")
    profile.add_preference("llm_provider_config.providers.gemini", "model_name", "test-gemini-model")
    
    provider = get_llm_provider_from_profile(profile)
    assert isinstance(provider, GeminiProvider), "Should select GeminiProvider based on profile."
    assert provider.model_name == "test-gemini-model"

# --- Evaluation for Task 19.3: Capability Assessment ---

def test_llm_capabilities_loading(tmp_path):
    """
    Assesses if LLMCapabilities can load predefined data for a known model.
    """
    # Create a dummy capabilities file
    # The root of the JSON file should be the map of model names to their capabilities
    caps_data = {
        "test-capabilities-model": {
            "context_window_tokens": 1000,
            "max_output_tokens": 100,
            "supports_function_calling": True
        }
    }
    caps_file = tmp_path / "model_capabilities.json"
    caps_file.write_text(json.dumps(caps_data))
    
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.PROVIDER_NAME = "MockProviderForCaps" # Set a provider name
    mock_provider.model_name = "test-capabilities-model"
    
    # Patch the default path to point to our temporary file
    with patch('core.llm_capabilities.CAPABILITIES_FILE', caps_file):
        capabilities = LLMCapabilities(provider=mock_provider, user_profile=MagicMock(spec=UserProfile))
        
        assert capabilities.get("context_window_tokens") == 1000
        assert capabilities.get("supports_function_calling") is True
        assert capabilities.get("non_existent_cap") is None, "Should return None for unknown capabilities."

def test_capability_assessor_gauntlet_run(tmp_path):
    """
    Assesses if the CapabilityAssessor correctly runs a test and generates a profile.
    """
    # Create a dummy gauntlet file
    gauntlet_data = {
        "json_adherence": [ # Match the structure in capability_assessor.py
            {
                "level": 1,
                "prompt": "Return a JSON object with a key 'status' set to 'ok'.",
                "validation_type": "is_json_exact",
                "expected_json": {"status": "ok"}
            }
        ]
    }
    gauntlet_file = tmp_path / "gauntlet.json"
    gauntlet_file.write_text(json.dumps(gauntlet_data))
    
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.is_available.return_value = True
    mock_provider.model_name = "test-gauntlet-model"
    mock_provider.PROVIDER_NAME = "MockProvider" # Add PROVIDER_NAME for profile
    
    # Assessor needs CodeGenerator and IdeaSynthesizer
    # IdeaSynthesizer is used for JSON adherence tests
    mock_idea_synth = MagicMock(spec=IdeaSynthesizer)
    mock_idea_synth.generate_text.return_value = '{"status": "ok"}' # Perfect response

    mock_deps = {
        "user_profile": MagicMock(spec=UserProfile),
        "memory_system": MagicMock(spec=Memory),
        "llm_provider": mock_provider,
        "project_contextualizer": MagicMock(spec=ProjectContextualizer),
    }
    
    with patch('core.capability_assessor.GAUNTLET_FILE_PATH', gauntlet_file):
        assessor = CapabilityAssessor(
            llm_provider=mock_provider,
            code_generator=MagicMock(spec=CodeGenerator), # Mock CodeGenerator if not directly used by this test path
            idea_synthesizer=mock_idea_synth
        )
        profile = assessor.run_gauntlet()

    assert "provider_name" in profile
    assert profile["model_name"] == "test-gauntlet-model"
    assert "details" in profile, "Profile should contain 'details' of test categories."
    assert "json_adherence" in profile["details"], "JSON adherence results should be in details."
    
    json_adherence_results = profile["details"]["json_adherence"]
    assert isinstance(json_adherence_results, list)
    assert len(json_adherence_results) == 1, "Should have one JSON adherence test result."
    
    test_result = json_adherence_results[0]
    assert test_result.get("level") == 1, "Test result should correspond to level 1."
    assert test_result.get("passed") is True, "The JSON adherence test should have passed."
