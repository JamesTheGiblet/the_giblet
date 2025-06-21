# core/llm_provider_base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    PROVIDER_NAME = "AbstractLLMProvider"

    def __init__(self, model_name: str | None = None, api_key: str | None = None, base_url: str | None = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url # For self-hosted like Ollama
        # This print is commented out as the concrete classes provide more specific initialization messages.
        # print(f" Initializing {self.PROVIDER_NAME} with model: {self.model_name or 'default'}")

    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generates text based on a prompt."""
        pass

    def is_available(self) -> bool:
        """Checks if the provider is configured and available."""
        return True # Default, subclasses should override