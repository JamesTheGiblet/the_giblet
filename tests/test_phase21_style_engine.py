# tests/test_phase21_style_engine.py

import pytest
from pathlib import Path
import sys
import json

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.style_preference import StylePreferenceManager, DEFAULT_STYLE_PREFERENCES

# --- Fixture for a temporary style preference file ---

@pytest.fixture
def temp_style_pref_file(tmp_path):
    """Provides a temporary, isolated file path for style preference tests."""
    return tmp_path / "test_style_preference.json"

# --- Evaluation for Task 21.1 & 21.3: Style Engine ---

def test_style_manager_persistence(temp_style_pref_file):
    """
    Assesses if the StylePreferenceManager correctly saves and loads preferences.
    """
    # 1. Create the first instance and set a custom preference.
    manager1 = StylePreferenceManager(file_path=temp_style_pref_file)
    manager1.set_preference("project.include_license", "Unlicense")
    manager1.set_preference("general_tone", "witty")

    # Verify it's set in the current instance
    assert manager1.get_preference("general_tone") == "witty"

    # 2. Create a second instance pointing to the same file.
    manager2 = StylePreferenceManager(file_path=temp_style_pref_file)

    # 3. Verify the preferences were loaded correctly from the file.
    assert manager2.get_preference("project.include_license") == "Unlicense"
    assert manager2.get_preference("general_tone") == "witty"

def test_style_manager_default_fallback(temp_style_pref_file):
    """
    Assesses that get_preference returns the default value for non-existent keys.
    """
    manager = StylePreferenceManager(file_path=temp_style_pref_file)
    
    # This key does not exist in the default preferences
    fallback_value = "default-value"
    retrieved_value = manager.get_preference("new_category.new_key", default=fallback_value)

    assert retrieved_value == fallback_value

def test_style_manager_reset_to_defaults(temp_style_pref_file):
    """
    Assesses the reset_to_defaults functionality.
    """
    # 1. Create an instance and change a preference
    manager = StylePreferenceManager(file_path=temp_style_pref_file)
    manager.set_preference("readme.default_style", "minimalist")
    assert manager.get_preference("readme.default_style") == "minimalist", "Preference should be updated before reset."

    # 2. Reset the preferences
    manager.reset_to_defaults()

    # 3. Verify that the preference has reverted to the default value
    default_readme_style = DEFAULT_STYLE_PREFERENCES["readme"]["default_style"]
    assert manager.get_preference("readme.default_style") == default_readme_style, "Preference should revert to default after reset."

    # 4. Verify that the underlying file also reflects the reset state
    with open(temp_style_pref_file, 'r') as f:
        data_on_disk = json.load(f)
    assert data_on_disk["readme"]["default_style"] == default_readme_style

