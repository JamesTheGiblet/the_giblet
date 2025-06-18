# core/idea_synth.py
from core.user_profile import UserProfile # Import UserProfile
from core.memory import Memory # Import Memory
from core.llm_provider_base import LLMProvider # Import LLMProvider

class IdeaSynthesizer:
    def __init__(self, user_profile: UserProfile, memory_system: Memory, llm_provider: LLMProvider):
        """
        Initializes the IdeaSynthesizer with a user profile, memory system, and an LLM provider.
        """
        self.user_profile = user_profile # Store the user_profile instance
        self.memory = memory_system # Store the memory_system instance
        self.llm_provider = llm_provider
        if self.llm_provider and self.llm_provider.is_available():
            print(f"🎨 Idea Synthesizer initialized using {self.llm_provider.PROVIDER_NAME} with model {self.llm_provider.model_name}.")
        else:
            print(f"⚠️ Idea Synthesizer: LLM provider {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'} is not available.")

    def generate_ideas(self, prompt: str, weird_mode: bool = False) -> str:
        """
        Generates ideas based on a user prompt, with an optional 'weird_mode'.
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            return f"Idea Synthesizer is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'})."

        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        company_name = self.user_profile.get_preference("general", "company_name", "their project")
        coding_style_summary = self.user_profile.get_preference("coding_style", "summary", "standard conventions")
        idea_persona = self.user_profile.get_preference("llm_settings", "idea_synth_persona", "creative and helpful")
        creativity_level = self.user_profile.get_preference("llm_settings", "idea_synth_creativity", 3)

        print(f"🎨 Synthesizing ideas for '{user_name}' regarding: '{prompt}'...")

        # The rest of the file is unchanged
        if weird_mode:
            final_prompt = f"""
            User prompt: "{prompt}"
            This is for a user named {user_name} working on {company_name}.
            They generally prefer a coding style described as: {coding_style_summary}.
            
            You are The Giblet's "weird_mode" creative engine.
            Brainstorm three bizarre, unconventional, or technically strange solutions.
            Think outside the box. Prioritize novelty over practicality.
            Format the output clearly.
            """
        else:
            creativity_description = "balanced between practical and novel"
            if creativity_level == 1:
                creativity_description = "highly practical and conventional"
            elif creativity_level == 2:
                creativity_description = "mostly practical with a touch of novelty"
            elif creativity_level == 4:
                creativity_description = "leaning towards novel and experimental"
            elif creativity_level == 5:
                creativity_description = "highly experimental and unconventional"

            final_prompt = f"""
            User prompt: "{prompt}"
            This is for a user named {user_name} working on {company_name}.
            They generally prefer a coding style described as: {coding_style_summary}.
            
            Adopt the following persona for your response: "{idea_persona}".
            Your approach to creativity should be: "{creativity_description}".
            Brainstorm three distinct solutions or ideas based on the user's prompt, keeping this persona and creativity level in mind.
            For each idea, briefly list its pros and cons.
            Format the output clearly.
            """
        
        try:
            response_text = self.llm_provider.generate_text(final_prompt)
            self.memory.remember('last_ai_interaction', {
                "module": "IdeaSynthesizer",
                "method": "generate_ideas",
                "prompt_summary": prompt[:100], # Store a summary of the input
                "output_summary": response_text[:150] # Store a summary of the output
            })
            return response_text
        except Exception as e:
            return f"❌ An error occurred during idea generation: {e}"


    # <<< NEW, more general-purpose method
    def generate_text(self, prompt: str) -> str:
        """
        Generates a direct text response from the model based on a given prompt.
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            return f"Idea Synthesizer is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'})."

        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        # Example of adding user context to a generic text generation prompt
        contextual_prompt = f"Considering the user is {user_name}:\n\n{prompt}"

        print(f"🎨 Generating text for {user_name} based on prompt...")

        try:
            response_text = self.llm_provider.generate_text(contextual_prompt)
            self.memory.remember('last_ai_interaction', {
                "module": "IdeaSynthesizer",
                "method": "generate_text",
                "prompt_summary": prompt[:100],
                "output_summary": response_text[:150]
            })
            return response_text
        except Exception as e:
            # Consider logging the full exception 'e' here for debugging
            return f"❌ An error occurred during text generation: {e}"