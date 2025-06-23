# core/llm_providers.py
import os
import google.generativeai as genai
import ollama
from core.llm_provider_base import LLMProvider
import logging

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    PROVIDER_NAME = "Gemini"

    def __init__(self, model_name: str = "gemini-1.5-flash-latest", api_key: str | None = None):
        # If api_key is not explicitly provided, try to get it from the environment variable
        resolved_api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        super().__init__(model_name=model_name, api_key=resolved_api_key)
        self.is_available_flag = False # Initialize to False
        if not self.api_key:
            logger.warning("[LLM] Gemini API key not found. Please set GEMINI_API_KEY environment variable or pass it during initialization.")
            self.client = None
        else:
            logger.info(f"[LLM] Initializing Gemini with model: {self.model_name}")
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                self.client.count_tokens("test") # Verify API key and model
                self.is_available_flag = True
                logger.info("[LLM] Gemini provider initialized successfully.")
            except Exception as e:
                logger.exception(f"[LLM] Failed to initialize Gemini provider: {e}") # Log full traceback
                self.client = None

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.client:
            logger.error("Attempted to generate text with an unavailable Gemini provider.")
            raise RuntimeError("Gemini provider is not available.") # Raise an exception
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        try:
            response = self.client.generate_content(prompt, generation_config=generation_config)
            # Check for safety ratings or empty responses
            if not response.candidates:
                logger.warning(f"Gemini returned no candidates for prompt: {prompt[:100]}...")
                return "" # Or raise a specific exception if no candidates is an error
            if hasattr(response.candidates[0], 'safety_ratings') and any(sr.blocked for sr in response.candidates[0].safety_ratings):
                logger.warning(f"Gemini response blocked by safety filters for prompt: {prompt[:100]}...")
                return "Response blocked due to safety concerns." # Or raise a specific exception
            
            return response.text
        except Exception as e:
            logger.exception(f"Error generating text with Gemini for prompt: {prompt[:100]}...") # Log full traceback
            raise RuntimeError(f"Error generating text with Gemini: {e}") # Re-raise as a more general runtime error

    def is_available(self) -> bool:
        return self.is_available_flag

class OllamaProvider(LLMProvider):
    PROVIDER_NAME = "Ollama"

    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434"):
        super().__init__(model_name=model_name, base_url=base_url)
        self.is_available_flag = False
        self.client = None
        if not self.base_url:
            logger.warning("[LLM] Ollama base URL not provided. Cannot initialize.")
            return
        try:
            logger.info(f"[LLM] Checking Ollama connection at {self.base_url}...")
            self.client = ollama.Client(host=self.base_url)
            # A lightweight check to see if the server is responsive.
            # The model will be pulled automatically by Ollama on first use if not present.
            self.client.list()
            self.is_available_flag = True
            logger.info(f"[LLM] Ollama provider connected. Using model: {self.model_name} (will be pulled on first use if not present).")
        except Exception as e:
            logger.exception(f"[LLM] Failed to initialize Ollama provider: {e}")
            self.client = None

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.client:
            logger.error("Attempted to generate text with an unavailable Ollama provider.")
            raise RuntimeError("Ollama provider is not available.")
        options = {
            "temperature": temperature,
            "num_predict": max_tokens
        }
        try:
            return self.client.generate(model=self.model_name, prompt=prompt, options=options)['response']
        except Exception as e:
            logger.exception(f"Error generating text with Ollama for prompt: {prompt[:100]}...")
            raise RuntimeError(f"Error generating text with Ollama: {e}")

    def is_available(self) -> bool:
        return self.is_available_flag