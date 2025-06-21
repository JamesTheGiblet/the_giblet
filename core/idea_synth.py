# core/idea_synth.py
import uuid
from typing import Any

# --- Core Module Imports ---
from core.llm_provider_base import LLMProvider
from core.memory import Memory
from core.user_profile import UserProfile
from core.project_contextualizer import ProjectContextualizer
from core.style_preference import StylePreferenceManager
from core.llm_capabilities import LLMCapabilities # Retaining this for advanced functionality

class IdeaSynthesizer:
    """
    Handles brainstorming and idea generation using an LLM, pulling from
    project context and user preferences for a tailored experience.
    """
    def __init__(self, user_profile: UserProfile,
                 memory_system: Memory,
                 llm_provider: LLMProvider,
                 project_contextualizer: ProjectContextualizer,
                 style_preference_manager: StylePreferenceManager):
        self.user_profile = user_profile
        self.memory = memory_system
        self.llm = llm_provider
        self.style_manager = style_preference_manager
        self.contextualizer = project_contextualizer
        self.capabilities = LLMCapabilities(provider=self.llm, user_profile=self.user_profile)

        if self.llm and self.llm.is_available():
            print(f"🎨 Idea Synthesizer initialized using {self.llm.PROVIDER_NAME} ({self.llm.model_name}).")
        else:
            print(f"⚠️ Idea Synthesizer: LLM provider {self.llm.PROVIDER_NAME if self.llm else 'None'} is not available.")

    def _construct_prompt(self, base_prompt: str, weird_mode: bool = False) -> str:
        """Constructs a detailed prompt for the LLM based on user profile and context."""
        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        project_context_summary = self.contextualizer.get_full_context() # Use get_full_context for comprehensive context
        general_style_tone = self.style_manager.get_preference("general_tone", "neutral")

        prompt = f"You are The Giblet's brainstorming module. Your goal is to generate creative and relevant ideas for a user named {user_name}.\n"
        prompt += f"Their preferred general communication tone is: '{general_style_tone}'.\n"
        prompt += f"Current project context: {project_context_summary}\n"

        if weird_mode:
            prompt += "Engage weird mode: Generate ONE unconventional, strange, and wonderful new software project idea. Be creative and unexpected.\n"
        else:
            idea_persona = self.user_profile.get_preference("llm_settings", "idea_synth_persona", "creative and helpful")
            prompt += f"Adopt the persona of a '{idea_persona}' assistant.\n"

        prompt += f"\nBased on all of this, please brainstorm ideas for the following topic: '{base_prompt}'\n"
        prompt += "CRITICAL: Return ONLY the raw idea itself, without any of your own conversational text, preamble, or formatting like 'Here's an idea:'."
        return prompt

    def generate_ideas(self, prompt_text: str, weird_mode: bool = False) -> str:
        """
        Generates ideas based on a prompt, optionally in "weird mode".
        """
        if not self.llm or not self.llm.is_available():
            return "Idea generation failed: LLM provider is not available."

        full_prompt = self._construct_prompt(prompt_text, weird_mode)

        try:
            response = self.llm.generate_text(
                full_prompt,
                max_tokens=self.capabilities.max_output_tokens
            )
            
            # Clean the response to prevent "prompt leak"
            lines = response.splitlines()
            idea_line = next((line.strip() for line in lines if line.strip()), None)
            clean_response = idea_line or response.strip()

            interaction_id = str(uuid.uuid4())
            self.memory.remember('last_ai_interaction', {
                "context_id": interaction_id,
                "type": "idea_generation",
                "prompt": full_prompt,
                "output": clean_response 
            })
            
            return clean_response

        except Exception as e:
            print(f"Error during idea generation: {e}")
            return f"Could not get a response from the LLM. Error: {e}"

    def generate_text(self, prompt: str) -> str:
        """
        Generates a direct text response from the model based on a given prompt,
        with light contextualization.
        """
        if not self.llm or not self.llm.is_available():
            return "Text generation failed: LLM provider is not available."

        # Simplified contextual prompt for general text generation
        contextual_prompt = f"""
        Project Context: {self.contextualizer.get_summary()}
        User's direct prompt: "{prompt}"
        """
        
        try:
            response_text = self.llm.generate_text(
                contextual_prompt,
                max_tokens=self.capabilities.max_output_tokens
            )
            clean_response = response_text.strip()

            interaction_id = str(uuid.uuid4())
            self.memory.remember('last_ai_interaction', {
                "context_id": interaction_id,
                "type": "text_generation",
                "prompt": contextual_prompt,
                "output": clean_response
            })
            return clean_response
        except Exception as e:
            print(f"Error during text generation: {e}")
            return f"An error occurred during text generation: {e}"
