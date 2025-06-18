# core/llm_capabilities.py
import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile
from core.memory import Memory  # For potentially storing/retrieving gauntlet results
import google.generativeai as genai # For Gemini metadata
import httpx # For Ollama metadata

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
        """
        Loads capabilities with the following priority (later steps override earlier ones for shared keys):
        1. Hardcoded defaults.
        2. Predefined map (model_capabilities.json).
        3. Provider API metadata.
        4. Gauntlet-generated profile's "determined_capabilities" (from UserProfile).
        """
        # 1. Initialize with hardcoded defaults
        temp_capabilities = {
            "context_window_tokens": 4096,
            "supports_function_calling": False,
            "max_output_tokens": 1024,
            "primary_modality": "text",
            "output_formats": ["text"],
            "strengths": []
        }
        print(f"ℹ️ Initializing with hardcoded default capabilities.")

        # 2. Load from predefined map (model_capabilities.json)
        try:
            if CAPABILITIES_FILE.exists():
                with open(CAPABILITIES_FILE, 'r', encoding='utf-8') as f:
                    all_known_caps = json.load(f)

                key_to_check = self.model_name
                # Try provider/model_name match if direct model name not found or if provider is known
                if self.provider_name.lower() != "unknown" and \
                   (self.model_name not in all_known_caps or f"{self.provider_name.lower()}/{self.model_name}" in all_known_caps):
                    combined_key = f"{self.provider_name.lower()}/{self.model_name}"
                    if combined_key in all_known_caps:
                        key_to_check = combined_key
                
                if key_to_check in all_known_caps:
                    print(f"ℹ️ Loading base capabilities from predefined map for '{key_to_check}'.")
                    temp_capabilities.update(all_known_caps[key_to_check])
        except Exception as e:
            print(f"\u26a0\ufe0f Could not load or parse {CAPABILITIES_FILE}: {e}")

        # 3. Query provider API for metadata to augment/override predefined
        if self.provider and self.provider.is_available():
            print(f"🔎 Attempting to fetch live metadata for {self.provider_name}/{self.model_name}...")
            api_fetched_caps = {}
            if self.provider_name == "Gemini":
                api_fetched_caps = self._fetch_gemini_metadata_dict()
            elif self.provider_name == "Ollama":
                api_fetched_caps = self._fetch_ollama_metadata_dict()
            
            if api_fetched_caps: # If any data was fetched
                print(f"ℹ️ Applying live metadata from API: {api_fetched_caps}")
                temp_capabilities.update(api_fetched_caps)

        # 4. Load Gauntlet-generated profile (highest priority for the keys it defines)
        if self.user_profile and self.provider_name != "unknown" and self.model_name != "unknown":
            gauntlet_profile_data = self.user_profile.get_gauntlet_profile(self.provider_name, self.model_name)
            if gauntlet_profile_data and "determined_capabilities" in gauntlet_profile_data:
                gauntlet_determined_caps = gauntlet_profile_data["determined_capabilities"]
                if isinstance(gauntlet_determined_caps, dict) and gauntlet_determined_caps: # Check if it's a non-empty dict
                    print(f"ℹ️ Applying determined capabilities from Gauntlet profile: {gauntlet_determined_caps}")
                    # Special handling for list-based capabilities like 'output_formats' or 'strengths' to merge, not just overwrite
                    for key, value in gauntlet_determined_caps.items():
                        if isinstance(value, list) and isinstance(temp_capabilities.get(key), list):
                            # Merge lists and remove duplicates
                            temp_capabilities[key] = list(set(temp_capabilities[key] + value))
                        else:
                            temp_capabilities[key] = value # Overwrite for other types
        
        self._capabilities = temp_capabilities
        print(f"\U0001F9E0 LLM Capabilities for {self.provider_name}/{self.model_name} loaded: {self._capabilities}")

    def _fetch_gemini_metadata_dict(self) -> Dict[str, Any]:
        fetched_caps = {}
        try:
            # Ensure genai is configured (it should be by GeminiProvider)
            model_info = genai.get_model(f"models/{self.model_name}") # This will raise if not found
            
            if hasattr(model_info, 'input_token_limit'):
                fetched_caps["context_window_tokens"] = model_info.input_token_limit
            if hasattr(model_info, 'output_token_limit'):
                fetched_caps["max_output_tokens"] = model_info.output_token_limit
            
            if hasattr(model_info, 'supported_generation_methods') and "functionCallingConfig" in model_info.supported_generation_methods:
                 fetched_caps["supports_function_calling"] = True
            # print(f"✅ Fetched Gemini metadata for {self.model_name}: {fetched_caps}") # Can be noisy
        except Exception as e:
            print(f"⚠️ Could not fetch Gemini metadata for {self.model_name}: {e}")
        return fetched_caps

    def _fetch_ollama_metadata_dict(self) -> Dict[str, Any]:
        fetched_caps = {}
        try:
            if not self.provider or not hasattr(self.provider, 'base_url') or not self.provider.base_url:
                return fetched_caps # Cannot proceed without base_url for OllamaProvider
            client = httpx.Client(base_url=self.provider.base_url)
            response = client.post("/api/show", json={"name": self.model_name}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Ollama's /api/show provides details in 'parameters' string, needs parsing
            # Example: "n_ctx              4096"
            # This is a simplified parsing; a more robust regex might be better.
            if "parameters" in data and isinstance(data["parameters"], str):
                params_str = data["parameters"]
                for line in params_str.split('\n'):
                    if "n_ctx" in line:
                        try:
                            fetched_caps["context_window_tokens"] = int(line.split()[-1])
                            break
                        except (ValueError, IndexError):
                            pass # Could not parse n_ctx
            # print(f"✅ Fetched Ollama metadata for {self.model_name}: {fetched_caps}") # Can be noisy
        except Exception as e:
            print(f"⚠️ Could not fetch Ollama metadata for {self.model_name}: {e}")
        return fetched_caps
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
