# core/idea_synth.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

class IdeaSynthesizer:
    def __init__(self):
        """
        Initializes the connection to the generative AI model, loading the API key from a .env file.
        """
        try:
            load_dotenv()
            
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

        print(f"🎨 Synthesizing ideas for: '{prompt}'...")

        # The rest of the file is unchanged
        if weird_mode:
            final_prompt = f"""
            User prompt: "{prompt}"
            
            You are The Giblet's "weird_mode" creative engine.
            Brainstorm three bizarre, unconventional, or technically strange solutions.
            Think outside the box. Prioritize novelty over practicality.
            Format the output clearly.
            """
        else:
            final_prompt = f"""
            User prompt: "{prompt}"
            
            You are a creative and helpful AI development partner.
            Brainstorm three distinct and practical solutions or ideas based on the user's prompt.
            For each idea, briefly list its pros and cons.
            Format the output clearly.
            """
        
        try:
            response = self.model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            return f"❌ An error occurred during idea generation: {e}"