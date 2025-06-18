# core/user_profile.py
from core.memory import Memory
from datetime import datetime # Import datetime

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
    def __init__(self, memory_system: Memory):
        """
        Initializes the UserProfile, loading data from the memory system.
        """
        self.memory = memory_system
        retrieved_data = self.memory.retrieve(PROFILE_MEMORY_KEY)

        # Check if the retrieved data is not a dictionary (e.g., it's the default "not found" string)
        if not isinstance(retrieved_data, dict):
            self.data = DEFAULT_PROFILE_STRUCTURE.copy() # Initialize with default structure
            print(f"👤 New user profile initialized with default structure (key '{PROFILE_MEMORY_KEY}' not found or invalid in memory).")
            self.save() # Save the initial empty profile
        else:
            self.data = retrieved_data
            print(f"👤 User profile loaded with {len(self.data)} top-level categories.")
    def get_all_data(self) -> dict:
        """Returns all profile data."""
        return self.data

    def add_preference(self, category: str, key: str, value: any):
        """
        Adds or updates a preference in a specific category.
        Example: add_preference("coding_style", "indent_size", 4)
        """
        if category not in self.data:
            self.data[category] = {}
        self.data[category][key] = value
        self.save()
        print(f"👤 Profile: '{category}.{key}' set to '{value}'.")

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
        # print("👤 User profile saved.") # Can be a bit noisy if called often

    def clear_profile(self):
        """Clears all user profile data."""
        self.data = {}
        self.save()
        print("👤 User profile cleared.")

    def add_feedback(self, rating: str, comment: str, context: dict | None = None):
        """
        Adds a feedback entry to the user profile.
        Rating can be 'positive', 'negative', 'neutral'.
        Context should be a dictionary describing what the feedback is about.
        """
        if "feedback_log" not in self.data:
            self.data["feedback_log"] = []
        
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "rating": rating.lower(),
            "comment": comment,
            "context": context or {} # Store the context of the AI interaction
        }
        self.data["feedback_log"].append(feedback_entry)
        self.save()
        print(f"🗣️ Feedback received: {rating} - '{comment[:50]}...'")

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