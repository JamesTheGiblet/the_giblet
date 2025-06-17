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
    "llm_settings": {
        "idea_synth_persona": "creative and helpful", # Default persona
        "code_gen_persona": "expert Python programmer"
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