# core/user_profile.py
from core.memory import Memory
from pathlib import Path # Make sure this is imported
from datetime import datetime # Import datetime
from typing import Optional # Ensure Optional is imported

PROFILE_MEMORY_KEY = "user_profile_data_v1" # Added a version to the key

DEFAULT_PROFILE_STRUCTURE = {
    "general": {
        "user_name": "",
        "company_name": ""
    },
    "coding_style": {
        "preferred_quote_type": "double", # e.g., single, double
        "indent_size": "4",
        "summary": "standard conventions" # A brief description
    },
    "llm_settings": { # Existing general LLM settings
        "idea_synth_persona": "creative and helpful", # Default persona
        "code_gen_persona": "expert Python programmer",
        "idea_synth_creativity": 3 # A scale, e.g., 1 (very practical) to 5 (very experimental)
    },
    "llm_provider_config": { # New section for provider selection and specific configs
        "active_provider": "gemini", # 'gemini' or 'ollama'
        "providers": {
            "gemini": {
                "api_key": "", # User can set this via UI/CLI, or it's read from .env by GeminiProvider
                "model_name": "gemini-1.5-flash-latest"
            },
            "ollama": {
                "base_url": "http://localhost:11434",
                "model_name": "mistral"
            }
        }
    }
}

class UserProfile:
    def __init__(self, memory_system: Memory, file_path: Optional[Path] = None):
        """
        Initializes the UserProfile, loading data from the memory system.
        Optionally, a specific file_path can be associated with this profile instance.
        """
        self.memory = memory_system
        
        if file_path:
            self.file_path = file_path
        else:
            # Default path if no specific file_path is provided for this instance
            self.file_path = Path(__file__).parent.parent / "data" / "user_profile.json"

        retrieved_data = self.memory.retrieve(PROFILE_MEMORY_KEY)
        # Check if the retrieved data is not a dictionary (e.g., it's the default "not found" string)
        if not isinstance(retrieved_data, dict):
            self.data = DEFAULT_PROFILE_STRUCTURE.copy() # Initialize with default structure
            print(f" New user profile initialized with default structure (key '{PROFILE_MEMORY_KEY}' not found or invalid in memory).")
            self.save() # Save the initial empty profile
        else:
            self.data = retrieved_data
            print(f" User profile loaded with {len(self.data)} top-level categories.")
    def get_all_data(self) -> dict:
        """Returns all profile data."""
        return self.data

    def add_preference(self, category: str, key: str, value: any):
        """
        Adds or updates a preference in a specific category.
        Example: add_preference("coding_style", "indent_size", 4)
        """
        # Handle dot-separated categories for nesting
        current_level = self.data
        if isinstance(category, str) and '.' in category:
            parts = category.split('.')
            for part in parts[:-1]:
                current_level = current_level.setdefault(part, {})
            final_category_key = parts[-1]
        else: # Original behavior for non-nested or already nested category
            final_category_key = category

        current_level.setdefault(final_category_key, {})[key] = value
        self.save() # Save after modification
        print(f" Profile: '{category if isinstance(category, str) else '.'.join(category)}.{key}' set to '{value}'.")

    def get_preference(self, category: str, key: str, default: any = None) -> any:
        """
        Retrieves a specific preference from a category.
        Returns the default value if the category or key is not found.
        """
        return self.data.get(category, {}).get(key, default)

    def save(self):
        """
        Saves the current profile data to long-term memory.
        """
        self.memory.commit(PROFILE_MEMORY_KEY, self.data)
        # print(" User profile saved.") # Can be a bit noisy if called often

    def clear_profile(self):
        """Clears all user profile data."""
        self.data = {}
        self.save()
        print(" User profile cleared.")

    def add_feedback(self, rating: int, comment: str, context_id: str | None = None):
        """
        Adds a feedback entry to the user profile.
        Rating should be an integer (e.g., 1-5).
        context_id is an optional string identifying the interaction.
        """
        if "feedback_log" not in self.data:
            self.data["feedback_log"] = []
        
        timestamp = datetime.now().isoformat()
        feedback_entry = {
            "timestamp": timestamp,
            "rating": rating, # Rating is now an int
            "comment": comment,
        }
        if context_id:
            feedback_entry["context_id"] = context_id # Use 'context_id' consistently

        self.data["feedback_log"].append(feedback_entry)
        self.save()
        print(f"🗣️ Feedback received: Rating {rating} - '{comment[:50]}...'")

    def get_feedback_log(self) -> list[dict]:
        """Retrieves the feedback log from the profile data."""
        return self.data.get("feedback_log", [])


    def save_gauntlet_profile(self, provider_name: str, model_name: str, profile_data: dict):
        """Saves a gauntlet-generated capability profile for a specific LLM."""
        if "llm_gauntlet_profiles" not in self.data:
            self.data["llm_gauntlet_profiles"] = {}
        
        # Ensure provider_name key exists
        if provider_name not in self.data["llm_gauntlet_profiles"]:
            self.data["llm_gauntlet_profiles"][provider_name] = {}
            
        self.data["llm_gauntlet_profiles"][provider_name][model_name] = profile_data
        self.save() # Use the existing save method of UserProfile
        print(f"💾 Gauntlet profile saved for {provider_name}/{model_name}.")

    def get_gauntlet_profile(self, provider_name: str, model_name: str) -> dict | None:
        """Retrieves a gauntlet-generated capability profile for a specific LLM."""
        profiles_root = self.data.get("llm_gauntlet_profiles")
        if not isinstance(profiles_root, dict): # Check if it's a dict
            return None
        
        provider_profiles = profiles_root.get(provider_name)
        if not isinstance(provider_profiles, dict): # Check if this level is a dict
            return None
        return provider_profiles.get(model_name)