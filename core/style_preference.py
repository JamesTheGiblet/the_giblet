# core/style_preference.py

"""
Manages user-specific style preferences for The Giblet.

This module handles loading, saving, and accessing preferences stored in
a JSON file (style_preference.json). These preferences define the user's
default formats, tones, and other stylistic choices for project generation
and other Giblet functionalities.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
import copy # For deepcopy
import logging

logger = logging.getLogger(__name__)

DEFAULT_STYLE_PREFERENCES = {
    "readme": {
        "default_style": "standard",  # e.g., "standard", "detailed", "minimalist"
        "default_tone": "professional",  # "professional", "casual", "witty", "neutral"
        "default_sections": ["Overview", "Features", "Getting Started", "Roadmap Link", "Contributing"]
    },
    "roadmap": {
        "default_format": "phase_based",  # "phase_based", "kanban_style", "simple_list"
        "default_tone": "neutral"
    },
    "project": {
        "default_repo_visibility": "private",  # "public", "private"
        "default_primary_language": "python",
        "include_gitignore": True,
        "include_license": "MIT" # or null/false
    },
    "general_tone": "neutral", # Overall preferred tone for communications
    "coding_style": {
        "preferred_formatter": "black", # "black", "autopep8", "yapf", null
        "docstring_format": "google" # "google", "numpy", "epytext", "reStructuredText"
    }
}


class StylePreferenceManager:
    """
    Manages loading, accessing, and saving user style preferences.
    """

    def __init__(self, file_path: Optional[Path] = None):
        """
        Initializes the StylePreferenceManager.

        Args:
            file_path: Optional path to the preferences JSON file.
                       If None, uses a default path within the project's data directory.
        """
        if file_path is None:
            # Assuming this file is in core/, so ../data/
            base_dir = Path(__file__).resolve().parent.parent
            self.file_path: Path = base_dir / "data" / "style_preference.json"
        else:
            self.file_path: Path = file_path

        self.preferences: Dict[str, Any] = {}
        self._load_preferences()

    def _ensure_file_exists(self) -> None:
        """Ensures the preference file and its directory exist, creating them if necessary."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                logger.info(f"Style preference file not found at {self.file_path}. Creating with defaults.")
                self.preferences = copy.deepcopy(DEFAULT_STYLE_PREFERENCES)
                self._save_preferences()
        except IOError as e:
            logger.error(f"Error ensuring style preference file exists at {self.file_path}: {e}")
            # Fallback to in-memory defaults if file system operations fail
            self.preferences = copy.deepcopy(DEFAULT_STYLE_PREFERENCES)


    def _load_preferences(self) -> None:
        """Loads preferences from the JSON file."""
        self._ensure_file_exists() # Ensures file is created with defaults if it doesn't exist

        # If _ensure_file_exists failed to create the file and fell back to in-memory defaults,
        # self.preferences is already set. If the file exists, we try to load it.
        if not self.file_path.exists() or not self.preferences: # Check if preferences are still empty
             return
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.preferences = json.load(f)
        except FileNotFoundError:
            # This case should ideally be handled by _ensure_file_exists
            logger.info(f"Style preference file not found at {self.file_path}. Initializing with defaults.")
            self.preferences = copy.deepcopy(DEFAULT_STYLE_PREFERENCES)
            self._save_preferences()
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.file_path}. Backing up and using defaults.")
            self._backup_corrupted_file()
            self.preferences = copy.deepcopy(DEFAULT_STYLE_PREFERENCES)
            self._save_preferences()
        except IOError as e:
            logger.error(f"Could not read style preference file {self.file_path}: {e}. Using defaults.")
            self.preferences = copy.deepcopy(DEFAULT_STYLE_PREFERENCES)

    def _backup_corrupted_file(self) -> None:
        """Backs up a corrupted preferences file."""
        if self.file_path.exists():
            backup_path = self.file_path.with_suffix(f".corrupted.{Path.cwd().name}.bak")
            try:
                self.file_path.rename(backup_path)
                logger.info(f"Backed up corrupted preference file to {backup_path}")
            except IOError as e:
                logger.error(f"Could not back up corrupted preference file {self.file_path}: {e}")

    def _save_preferences(self) -> None:
        """Saves the current preferences to the JSON file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=4)
        except IOError as e:
            logger.error(f"Could not write style preference file {self.file_path}: {e}")

    def get_preference(self, key_path: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a preference value using a dot-separated key path.

        Args:
            key_path: The dot-separated path to the preference (e.g., "readme.default_style").
            default: The value to return if the key is not found.

        Returns:
            The preference value or the default.
        """
        keys = key_path.split('.')
        value = self.preferences
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set_preference(self, key_path: str, value: Any) -> None:
        """
        Sets a preference value using a dot-separated key path.
        Creates necessary dictionaries if parts of the path do not exist.

        Args:
            key_path: The dot-separated path to the preference (e.g., "readme.default_style").
            value: The value to set.
        """
        keys = key_path.split('.')
        current_level = self.preferences
        for i, key in enumerate(keys[:-1]):
            if key not in current_level or not isinstance(current_level[key], dict):
                current_level[key] = {}
            current_level = current_level[key]
        current_level[keys[-1]] = value
        self._save_preferences()

    def get_all_preferences(self) -> Dict[str, Any]:
        """Returns a copy of all current preferences."""
        return self.preferences.copy()

    def reset_to_defaults(self) -> None:
        """Resets all preferences to their default values and saves."""
        self.preferences = copy.deepcopy(DEFAULT_STYLE_PREFERENCES)
        self._save_preferences()
        logger.info(f"Style preferences reset to defaults and saved to {self.file_path}")

    def set_preferences_for_category(self, category: str, settings: Dict[str, Any]) -> None:
        """
        Sets multiple preferences for a given category.

        Args:
            category: The category name (e.g., "readme", "roadmap").
            settings: A dictionary of key-value pairs to set within that category.
        """
        if category not in self.preferences or not isinstance(self.preferences.get(category), dict):
            self.preferences[category] = {} # Ensure the category exists as a dictionary

        for key, value in settings.items():
            self.preferences[category][key] = value
        
        self._save_preferences()
        logger.info(f"Style preferences for category '{category}' updated.")
# Example Usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test with a temporary file
    temp_pref_file = Path("./temp_style_preference.json")
    manager = StylePreferenceManager(file_path=temp_pref_file)

    print("Initial preferences:", json.dumps(manager.get_all_preferences(), indent=2))

    manager.set_preference("readme.default_tone", "witty")
    manager.set_preference("project.new_setting", True)
    manager.set_preference("coding_style.tab_size", 4)

    print("\nUpdated readme tone:", manager.get_preference("readme.default_tone"))
    print("New project setting:", manager.get_preference("project.new_setting"))
    print("Tab size:", manager.get_preference("coding_style.tab_size"))
    print("Non-existent key:", manager.get_preference("non.existent.key", "fallback"))

    print("\nAll preferences after updates:", json.dumps(manager.get_all_preferences(), indent=2))

    manager.reset_to_defaults()
    print("\nPreferences after reset:", json.dumps(manager.get_all_preferences(), indent=2))

    # Clean up the temporary file
    if temp_pref_file.exists():
        temp_pref_file.unlink()