# core/llm_providers/ollama_provider.py
import httpx
import json
from core.llm_provider_base import LLMProvider

class OllamaProvider(LLMProvider):
    PROVIDER_NAME = "Ollama"

    def __init__(self, model_name: str = 'mistral', base_url: str = "http://localhost:11434"):
        super().__init__(model_name=model_name, base_url=base_url)
        self.client = httpx.Client(base_url=self.base_url)
        if not self.check_ollama_availability():
             print(f" {self.PROVIDER_NAME} server at {self.base_url} might not be reachable or model '{self.model_name}' not available.")
        else:
            print(f" {self.PROVIDER_NAME} provider initialized for model '{self.model_name}' at {self.base_url}.")

    def check_ollama_availability(self):
        try:
            self.client.get("/") # Simple check if server is up
            # Optionally, check if model exists: self.client.post("/api/show", json={"name": self.model_name})
            return True
        except httpx.RequestError:
            return False

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str: # Ollama uses 'num_predict' for max_tokens
        if not self.is_available(): # is_available could be enhanced to re-check server
            return f"# {self.PROVIDER_NAME} not available or model '{self.model_name}' not found."
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False, # For simplicity, not streaming
                "options": {"temperature": temperature, "num_predict": max_tokens}
            }
            response = self.client.post("/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", f"# Error: No response field from {self.PROVIDER_NAME}")
        except Exception as e:
            return f"# Error during {self.PROVIDER_NAME} generation: {e}"

    def is_available(self) -> bool:
        return self.check_ollama_availability() # Re-check on demand