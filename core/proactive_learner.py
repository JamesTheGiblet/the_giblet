import json
from typing import List, Dict, Any, Optional

# Import the actual UserProfile class
from .user_profile import UserProfile

# Placeholder for UserProfile for standalone development/testing.
# In the actual project, you would import the real UserProfile.
class UserProfilePlaceholder: # This class can remain for testing or if direct file access is needed elsewhere.
    def __init__(self, profile_path="data/user_profile.json"):
        self.profile_path = profile_path
        self.data = {"preferences": {}, "feedback_log": []}
        self._load()

    def _load(self):
        try:
            with open(self.profile_path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            # In a real scenario, this might be an error or handled by UserProfile's creation
            print(f"Warning: Profile file {self.profile_path} not found. Using empty data.")
            self.data = {"preferences": {}, "feedback_log": []}
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {self.profile_path}. Using empty data.")
            self.data = {"preferences": {}, "feedback_log": []}

    def get_feedback_log(self) -> List[Dict[str, Any]]:
        return self.data.get("feedback_log", [])

    def get_preference(self, key: str, default: Any = None) -> Any: # For UserProfilePlaceholder, preferences are flat
        return self.data.get("preferences", {}).get(key, default)

class ProactiveLearner:
    """
    Analyzes user feedback and profile data to suggest adaptations
    for prompt templates or agent behaviors.
    """

    def __init__(self, user_profile: UserProfile): # Changed to actual UserProfile
        """
        Initializes the ProactiveLearner.

        Args:
            user_profile: An instance of UserProfile to access feedback and preferences.
        """
        self.user_profile = user_profile

    def analyze_feedback(self) -> Dict[str, Any]:
        """
        Analyzes the feedback log to identify patterns.

        Returns:
            A dictionary containing analysis results.
        """
        feedback_log = self.user_profile.get_feedback_log()
        analysis_results = {
            "feedback_summary_by_context": {} # e.g., context_id: {"avg_rating": X, "count": Y, "comments": []}
        }

        if not feedback_log:
            return analysis_results

        for item in feedback_log:
            context_id = item.get("context_id", "general") # 'context_id' links feedback to a specific prompt/agent
            rating = item.get("rating")
            comment = item.get("comment", "")

            if context_id not in analysis_results["feedback_summary_by_context"]:
                analysis_results["feedback_summary_by_context"][context_id] = {
                    "ratings": [], "comments": [], "count": 0
                }
            
            summary = analysis_results["feedback_summary_by_context"][context_id]
            summary["count"] += 1
            if rating is not None:
                # Ensure rating is float before appending
                try:
                    summary["ratings"].append(float(rating))
                except ValueError:
                    print(f"Warning: Could not convert rating '{rating}' to float for context '{context_id}'. Skipping this rating.")
            if comment:
                summary["comments"].append(comment.lower())
        
        for context_id, data in analysis_results["feedback_summary_by_context"].items():
            if data["ratings"]:
                # Ensure ratings are float for division (already done above, but good to be safe)
                numeric_ratings = [r for r in data["ratings"] if isinstance(r, (int, float))]
                if numeric_ratings:
                    data["avg_rating"] = sum(numeric_ratings) / len(numeric_ratings)
                else:
                    data["avg_rating"] = None # Or some default if no valid ratings
            # More sophisticated comment analysis (NLP, keyword extraction) could be added here.

        return analysis_results

    def analyze_user_profile_preferences(self) -> Dict[str, Any]:
        """
        Analyzes user profile preferences relevant to prompts/behaviors.

        Returns:
            A dictionary of relevant preferences.
        """
        preferences = {}
        # Accessing preferences correctly from UserProfile, assuming they are in 'llm_settings'
        # UserProfile.get_preference takes category and key
        preferences["ai_verbosity"] = self.user_profile.get_preference("llm_settings", "ai_verbosity")
        preferences["ai_tone"] = self.user_profile.get_preference("llm_settings", "ai_tone")
        preferences["idea_synth_persona"] = self.user_profile.get_preference("llm_settings", "idea_synth_persona")
        # Add other relevant preferences from UserProfile as they are defined
        return {k: v for k, v in preferences.items() if v is not None}

    def generate_suggestions(self) -> List[str]:
        """
        Generates actionable suggestions based on feedback and profile analysis.

        Returns:
            A list of string suggestions.
        """
        suggestions = []
        feedback_analysis = self.analyze_feedback()
        profile_prefs = self.analyze_user_profile_preferences()

        # Suggestions from feedback analysis
        for context_id, data in feedback_analysis.get("feedback_summary_by_context", {}).items():
            avg_rating = data.get("avg_rating")
            count = data.get("count")
            if avg_rating is not None and count >= 3: # Only suggest if there's enough data
                if avg_rating < 2.5:
                    suggestions.append(
                        f"Consider reviewing prompts/behavior for '{context_id}'. "
                        f"It has a low average rating ({avg_rating:.2f} from {count} entries)."
                    )
                elif avg_rating > 4.0:
                    # Look for common themes in positive comments for highly rated contexts
                    # For example, if "detailed" or "thorough" is common in comments:
                    positive_comments_text = " ".join(data.get("comments", []))
                    if "detail" in positive_comments_text or "thorough" in positive_comments_text:
                        suggestions.append(
                            f"Users appreciate detailed/thorough responses for '{context_id}'. "
                            "Ensure prompts for this context continue to encourage this."
                        )

        # Suggestions from profile preferences
        if profile_prefs.get("ai_verbosity") == "low":
            suggestions.append("Your preference is for 'low' AI verbosity. Review prompts to ensure concise outputs where appropriate.")
        if profile_prefs.get("ai_tone"):
            suggestions.append(f"Your preferred AI tone is '{profile_prefs['ai_tone']}'. Ensure prompts align with this.")
        if profile_prefs.get("idea_synth_persona"):
            suggestions.append(
                f"For idea synthesis, you prefer the '{profile_prefs['idea_synth_persona']}' persona. "
                "Ensure IdeaSynthesizer prompts leverage this effectively."
            )

        if not suggestions:
            return ["No specific proactive suggestions at this time. Keep providing feedback to help Giblet learn!"]
        
        return list(set(suggestions)) # Return unique suggestions
