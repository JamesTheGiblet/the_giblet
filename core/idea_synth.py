# core/idea_synth.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from core.user_profile import UserProfile # Import UserProfile
from core.memory import Memory # Import Memory

class IdeaSynthesizer:
    def __init__(self, user_profile: UserProfile, memory_system: Memory): # Add memory_system
        """
        Initializes the connection to the generative AI model, loading the API key from a .env file.
        """
        self.user_profile = user_profile # Store the user_profile instance
        self.memory = memory_system # Store the memory_system instance
        try:
            # <<< FIX: Explicitly use utf-8 encoding to read the .env file
            load_dotenv(encoding='utf-8')
            
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")
            
            genai.configure(api_key=self.api_key)
            # <<< CHANGED: Updated the model name to a current, valid model
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            print("🎨 Idea Synthesizer initialized with Gemini-1.5-Flash.")
        except Exception as e:
            print(f"❌ Failed to initialize Idea Synthesizer: {e}")
            self.model = None

    def generate_ideas(self, prompt: str, weird_mode: bool = False) -> str:
        """
        Generates ideas based on a user prompt, with an optional 'weird_mode'.
        """
        if not self.model:
            return "Idea Synthesizer is not available."

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
            response = self.model.generate_content(final_prompt)
            self.memory.remember('last_ai_interaction', {
                "module": "IdeaSynthesizer",
                "method": "generate_ideas",
                "prompt_summary": prompt[:100], # Store a summary of the input
                "output_summary": response.text[:150] # Store a summary of the output
            })
            return response.text
        except Exception as e:
            return f"❌ An error occurred during idea generation: {e}"


    # <<< NEW, more general-purpose method
    def generate_text(self, prompt: str) -> str:
        """
        Generates a direct text response from the model based on a given prompt.
        """
        if not self.model:
            return "Idea Synthesizer is not available."

        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        # Example of adding user context to a generic text generation prompt
        contextual_prompt = f"Considering the user is {user_name}:\n\n{prompt}"

        print(f"🎨 Generating text for {user_name} based on prompt...")

        try:
            response = self.model.generate_content(contextual_prompt) # Use contextual_prompt
            self.memory.remember('last_ai_interaction', {
                "module": "IdeaSynthesizer",
                "method": "generate_text",
                "prompt_summary": prompt[:100],
                "output_summary": response.text[:150]
            })
            return response.text
        except Exception as e:
            # Consider logging the full exception 'e' here for debugging
            return f"❌ An error occurred during text generation: {e}"