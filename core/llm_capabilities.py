# core/llm_capabilities.py
import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile
from core.memory import Memory  # For potentially storing/retrieving gauntlet results

CAPABILITIES_FILE = Path(__file__).parent.parent / "data" / "model_capabilities.json"

class LLMCapabilities:
    def __init__(self, provider: Optional[LLMProvider] = None, user_profile: Optional[UserProfile] = None):
        self.provider = provider
        self.user_profile = user_profile
        self.model_name = provider.model_name if provider else "unknown"
        self.provider_name = provider.PROVIDER_NAME if provider else "unknown"
        self._capabilities: Dict[str, Any] = {}
        # self.memory = Memory()  # If you decide to store gauntlet results in memory
        self._load_capabilities()

    def _load_capabilities(self):
        # Priority:
        # 1. (Future) Gauntlet-generated profile from memory/UserProfile
        # 2. Predefined map (model_capabilities.json)
        # 3. (Future) Provider API metadata
        # 4. Defaults

        try:
            if CAPABILITIES_FILE.exists():
                with open(CAPABILITIES_FILE, 'r', encoding='utf-8') as f:
                    all_known_caps = json.load(f)

                # Try direct model name match first
                if self.model_name in all_known_caps:
                    self._capabilities.update(all_known_caps[self.model_name])
                # Try provider/model_name match (e.g., "ollama/mistral")
                elif f"{self.provider_name.lower()}/{self.model_name}" in all_known_caps:
                    self._capabilities.update(all_known_caps[f"{self.provider_name.lower()}/{self.model_name}"])

        except Exception as e:
            print(f"\u26a0\ufe0f Could not load or parse {CAPABILITIES_FILE}: {e}")

        # (Future) Query provider API for metadata if self.provider is available
        # Example: if self.provider_name == "Gemini": self._fetch_gemini_metadata()

        # Set some defaults if nothing specific is found
        self._capabilities.setdefault("context_window_tokens", 4096)
        self._capabilities.setdefault("supports_function_calling", False)
        self._capabilities.setdefault("max_output_tokens", 1024) # Default max output tokens
        self._capabilities.setdefault("primary_modality", "text")
        self._capabilities.setdefault("output_formats", ["text"])
        self._capabilities.setdefault("strengths", [])

        print(f"\U0001F9E0 LLM Capabilities for {self.provider_name}/{self.model_name} loaded: {self._capabilities}")

    def get(self, capability_name: str, default: Any = None) -> Any:
        return self._capabilities.get(capability_name, default)

    @property
    def context_window(self) -> int:
        return self.get("context_window_tokens", 4096)

    @property
    def supports_function_calling(self) -> bool:
        return self.get("supports_function_calling", False)

    @property
    def max_output_tokens(self) -> int:
        return self.get("max_output_tokens", 1024)

    # Add more properties for commonly accessed capabilities
