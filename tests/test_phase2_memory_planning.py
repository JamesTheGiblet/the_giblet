# tests/test_phase3_creative.py

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.idea_synth import IdeaSynthesizer
from core.user_profile import UserProfile
from core.memory import Memory
from core.llm_provider_base import LLMProvider
from core.project_contextualizer import ProjectContextualizer
from core.style_preference import StylePreferenceManager
from core.llm_capabilities import LLMCapabilities # Import for patching if needed

# --- Mock Fixtures for Dependencies ---

@pytest.fixture
def mock_llm_provider():
    """Mocks the LLMProvider to return a predictable response."""
    mock = MagicMock(spec=LLMProvider)
    mock.is_available.return_value = True
    
    # FIX: The LLMCapabilities class requires the provider to have a model_name.
    # We add this attribute to our mock to satisfy the dependency.
    mock.model_name = "mock-model-for-testing"
    
    # The generate_text method will be configured in each test
    return mock

@pytest.fixture
def mock_dependencies(mock_llm_provider):
    """Provides a dictionary of mocked dependencies needed by IdeaSynthesizer."""
    # Since LLMCapabilities is now a dependency of IdeaSynthesizer, we should mock it too,
    # or ensure our mock provider has everything it needs. Let's stick to fixing the provider.
    return {
        "user_profile": MagicMock(spec=UserProfile),
        "memory_system": MagicMock(spec=Memory),
        "llm_provider": mock_llm_provider,
        "project_contextualizer": MagicMock(spec=ProjectContextualizer),
        "style_preference_manager": MagicMock(spec=StylePreferenceManager)
    }

# --- Evaluation for Task 3.1 & 3.2: Creative Intelligence ---

def test_idea_synthesizer_standard_generation(mock_dependencies):
    """
    Assesses the stability of the standard idea generation process.
    - Verifies the method runs without error.
    - Checks that a non-empty string is returned.
    """
    mock_dependencies["llm_provider"].generate_text.return_value = "A standard, sensible idea."
    
    idea_synth = IdeaSynthesizer(**mock_dependencies)
    
    prompt = "a new python project"
    ideas = idea_synth.generate_ideas(prompt, weird_mode=False)
    
    mock_dependencies["llm_provider"].generate_text.assert_called_once()
    
    assert isinstance(ideas, str)
    assert len(ideas) > 0
    assert ideas == "A standard, sensible idea."

def test_idea_synthesizer_weird_mode_prompting(mock_dependencies):
    """
    Assesses whether 'weird_mode' correctly influences the prompt sent to the LLM.
    """
    mock_dependencies["llm_provider"].generate_text.return_value = "A weird, chaotic idea."

    idea_synth = IdeaSynthesizer(**mock_dependencies)

    prompt = "a new game"
    idea_synth.generate_ideas(prompt, weird_mode=True)
    
    mock_dependencies["llm_provider"].generate_text.assert_called_once()
    
    call_args, call_kwargs = mock_dependencies["llm_provider"].generate_text.call_args
    final_prompt = call_kwargs.get('prompt', call_args[0])
    
    assert "weird" in final_prompt.lower() or "unconventional" in final_prompt.lower(), \
        "The prompt should contain keywords indicating weird_mode is active."
    assert "standard" not in final_prompt.lower(), \
        "The prompt should not contain standard-mode language when weird_mode is active."

