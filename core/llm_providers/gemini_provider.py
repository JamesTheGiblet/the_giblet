# core/llm_providers/gemini_provider.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from core.llm_provider_base import LLMProvider

class GeminiProvider(LLMProvider):
    PROVIDER_NAME = "Gemini"

    def __init__(self, model_name: str = 'gemini-1.5-flash-latest', api_key: str | None = None):
        super().__init__(model_name=model_name, api_key=api_key)
        self.model = None
        try:
            load_dotenv(encoding='utf-8')
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in .env or provided.")
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✅ {self.PROVIDER_NAME} provider initialized with model '{self.model_name}'.")
        except Exception as e:
            print(f"❌ Failed to initialize {self.PROVIDER_NAME} provider: {e}")
            self.model = None

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str: # Gemini uses 'temperature' implicitly via GenerationConfig
        if not self.is_available():
            return f"# {self.PROVIDER_NAME} model not available."
        try:
            # Note: Gemini API's generate_content doesn't directly take max_tokens in the same way as OpenAI.
            # Temperature is part of generation_config.
            response = self.model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=temperature))
            return response.text
        except Exception as e:
            return f"# Error during {self.PROVIDER_NAME} generation: {e}"

    def is_available(self) -> bool:
        return self.model is not None