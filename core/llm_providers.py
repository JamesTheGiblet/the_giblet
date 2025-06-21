# core/llm_providers.py
import os
import google.generativeai as genai
import ollama
from core.llm_provider_base import LLMProvider

class GeminiProvider(LLMProvider):
    PROVIDER_NAME = "Gemini"

    def __init__(self, model_name: str = "gemini-1.5-flash-latest", api_key: str | None = None):
        super().__init__(model_name=model_name, api_key=api_key)
        self.is_available_flag = False
        if not self.api_key:
            print("[LLM] Gemini API key not found. Please set GEMINI_API_KEY environment variable or pass it during initialization.")
            self.client = None
        else:
            print(f"[LLM] Initializing Gemini with model: {self.model_name}")
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                self.client.count_tokens("test") # Verify API key and model
                self.is_available_flag = True
                print("[LLM] Gemini provider initialized successfully.")
            except Exception as e:
                print(f"[LLM] Failed to initialize Gemini provider: {e}")
                self.client = None

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.client: return "Gemini provider is not available."
        try:
            return self.client.generate_content(prompt).text
        except Exception as e:
            return f"Error generating text with Gemini: {e}"

    def is_available(self) -> bool:
        return self.is_available_flag

class OllamaProvider(LLMProvider):
    PROVIDER_NAME = "Ollama"

    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434"):
        super().__init__(model_name=model_name, base_url=base_url)
        self.is_available_flag = False
        try:
            print(f"[LLM] Initializing Ollama with model: {self.model_name} at {self.base_url}")
            self.client = ollama.Client(host=self.base_url)
            self.client.pull(self.model_name) # Ensure model is downloaded
            self.is_available_flag = True
            print("[LLM] Ollama provider initialized successfully.")
        except Exception as e:
            print(f"[LLM] Failed to initialize Ollama provider: {e}")
            self.client = None

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.client: return "Ollama provider is not available."
        try:
            return self.client.generate(model=self.model_name, prompt=prompt)['response']
        except Exception as e:
            return f"Error generating text with Ollama: {e}"

    def is_available(self) -> bool:
        return self.is_available_flag