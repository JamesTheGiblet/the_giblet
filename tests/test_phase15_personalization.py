# tests/test_phase15_personalization.py

import pytest
from pathlib import Path
import sys
import json
from unittest.mock import MagicMock, patch

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.user_profile import UserProfile
from core.memory import Memory
from core.idea_synth import IdeaSynthesizer
from core.llm_provider_base import LLMProvider
from core.project_contextualizer import ProjectContextualizer
from core.style_preference import StylePreferenceManager

# --- Fixtures ---

@pytest.fixture
def temp_user_profile(tmp_path):
    """Creates a UserProfile instance with a temporary data file."""
    # UserProfile depends on Memory, so we need a dummy one.
    dummy_memory = Memory(file_path=tmp_path / "dummy_memory.json")
    
    # Create the UserProfile with its own temp file
    profile_file = tmp_path / "test_user_profile.json"
    user_profile = UserProfile(memory_system=dummy_memory, file_path=profile_file)
    
    # Ensure a clean state before the test
    user_profile.data = {"general": {}}
    user_profile.save() # Correct method name
    
    return user_profile

# --- Evaluation for Task 15.1: User Profile Model ---

def test_user_profile_persistence(temp_user_profile):
    """
    Assesses if the UserProfile can correctly save and load preferences.
    """
    # 1. Set a preference in the first instance
    category = "testing"
    key = "preference_A"
    value = "test_value_123"
    temp_user_profile.add_preference(category, key, value)

    # Verify it's set in the current instance
    assert temp_user_profile.get_preference(category, key) == value

    # 2. Create a new UserProfile instance pointing to the same file to test loading
    # The UserProfile saves to the Memory system, not directly to its own file_path
    # So, we need to use the same Memory instance.
    new_user_profile = UserProfile(memory_system=temp_user_profile.memory, file_path=temp_user_profile.file_path)
    
    # 3. Verify the preference was loaded from the memory system
    assert new_user_profile.get_preference(category, key) == value, "Preference should persist across instances via the memory system."

# --- Evaluation for Task 15.2: Dynamic Prompt Personalization ---

def test_idea_synthesizer_uses_user_profile_persona(temp_user_profile):
    """
    Assesses if the IdeaSynthesizer incorporates the user's preferred persona into its prompt.
    """
    # 1. Set a specific persona in the user profile
    test_persona = "a sarcastic and world-weary robot"
    temp_user_profile.add_preference("llm_settings", "idea_synth_persona", test_persona)

    # 2. Set up mocked dependencies for IdeaSynthesizer
    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.is_available.return_value = True
    mock_llm.model_name = "mock-persona-model"
    
    # Mock ProjectContextualizer and StylePreferenceManager
    mock_project_contextualizer = MagicMock(spec=ProjectContextualizer)
    mock_project_contextualizer.get_full_context.return_value = "Mock project context."
    
    mock_style_manager = MagicMock(spec=StylePreferenceManager)
    mock_style_manager.get_preference.return_value = "neutral" # Default for general_tone

    dependencies = {
        "user_profile": temp_user_profile,
        "memory_system": MagicMock(spec=Memory),
        "llm_provider": mock_llm,
        "project_contextualizer": mock_project_contextualizer,
        "style_preference_manager": mock_style_manager
    }
    
    # The IdeaSynthesizer __init__ may try to access methods on the mocked dependencies
    # that don't exist. We can patch LLMCapabilities to prevent this.
    with patch('core.idea_synth.LLMCapabilities') as mock_caps:
        # Ensure the mocked LLMCapabilities instance has max_output_tokens
        mock_caps_instance = mock_caps.return_value
        mock_caps_instance.max_output_tokens = 1024 
        idea_synth = IdeaSynthesizer(**dependencies)
    
    # 3. Call the generate method
    idea_synth.generate_ideas("a new todo app")

    # 4. Assert that the prompt sent to the LLM contains the custom persona
    mock_llm.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm.generate_text.call_args
    final_prompt = call_kwargs.get('prompt', call_args[0])

    assert test_persona in final_prompt, "The custom persona from the user profile was not used in the prompt."

# --- Evaluation for Task 15.3: Interaction Feedback Loop ---

def test_user_profile_feedback_loop(temp_user_profile):
    """
    Assesses if the UserProfile correctly logs feedback.
    """
    rating = 1  # "bad"
    comment = "The output was not helpful at all."
    context_id = "test_generation_1"
    
    
    # 1. Add feedback using the dedicated method
    temp_user_profile.add_feedback(rating, comment, context_id)
    
    # 2. Retrieve the profile data from the Memory instance to ensure it was saved correctly
    # The UserProfile saves to memory using PROFILE_MEMORY_KEY
    profile_data = temp_user_profile.memory.retrieve("user_profile_data_v1")

    # 3. Verify the feedback was logged in the retrieved data
    assert "feedback_log" in profile_data, "Profile data retrieved from memory should contain a 'feedback_log' key."
    feedback_log = profile_data["feedback_log"]
    
    assert isinstance(feedback_log, list)
    assert len(feedback_log) == 1, "Exactly one feedback entry should have been logged in memory."
    
    entry = feedback_log[0]
    assert entry["rating"] == rating
    assert entry["comment"] == comment
    assert entry["context_id"] == context_id
    assert "timestamp" in entry, "Feedback entry in memory must include a timestamp."
