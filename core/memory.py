# core/memory.py
import json
import os
from pathlib import Path
from typing import Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class Memory:
    def __init__(self, file_path: Optional[Path] = None, checkpoint_directory: Optional[Path] = None):
        """
        Initializes the Memory module, connecting to Redis if configured,
        otherwise falling back to local JSON files.
        """
        self.backend_type = os.getenv("GIBLET_MEMORY_BACKEND", "json").lower()
        
        # Store provided paths or fall back to defaults
        self._long_term_memory_file_path = file_path
        self._checkpoint_directory = checkpoint_directory
        self.redis_client = None

        # --- Session Memory (volatile) ---
        self.session_memory = {}
        # --- Cache for JSON-based long-term memory ---
        self._long_term_data_cache = {}

        # --- Long-Term Memory (persistent) ---
        if self.backend_type == "redis" and REDIS_AVAILABLE:
            try:
                redis_url = os.getenv("GIBLET_REDIS_URL", "redis://localhost:6379")
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping() # Check connection
                self.long_term_memory_key = "giblet:long_term_memory"
                print(f"🧠 Memory module connected to Redis at {redis_url}.")
            except Exception as e:
                print(f"❌ Redis connection failed: {e}. Falling back to JSON.")
                self.backend_type = "json"

        if self.backend_type == "json":
            if self._long_term_memory_file_path is None:
                self._long_term_memory_file_path = Path(__file__).parent.parent / "data/memory.json"
            self.long_term_memory_path = self._long_term_memory_file_path
            self.long_term_memory_path.touch(exist_ok=True)
            print("[MEM] Memory module initialized with local JSON backend.")

        self._load_long_term_data()

    def _load_long_term_data(self):
        """Loads the long-term memory from the configured backend."""
        if self.redis_client:
            # In Redis, data is "live", but we can log that we're ready.
            print("   (Redis backend is live, no initial load needed)")
        else: # JSON backend
            try:
                # Load into the dedicated cache, not session_memory
                content = self.long_term_memory_path.read_text(encoding='utf-8')
                if content:
                    self._long_term_data_cache.update(json.loads(content))
                    print(f"   (JSON long-term data loaded into cache from {self.long_term_memory_path.name})")
            except (json.JSONDecodeError, FileNotFoundError):
                self._long_term_data_cache.update({}) # Initialize cache if file is empty/missing/corrupt
                print(f"   (JSON long-term data cache initialized as empty; file issue or new setup for {self.long_term_memory_path.name})")

    def remember(self, key: str, value):
        """Saves a key-value pair to the current session's memory."""
        self.session_memory[key] = value
        print(f"🧠 OK. I'll remember '{key}' for this session.")

    def recall(self, key: str):
        """Recalls a value from the current session's memory."""
        return self.session_memory.get(key, f"I don't have a memory for '{key}'.")

    def commit(self, key: str, value):
        """Commits a specific key-value pair to long-term memory."""
        # Also remember it in the current session
        self.remember(key, value)

        if self.redis_client:
            self.redis_client.hset(self.long_term_memory_key, key, json.dumps(value))
            print(f"✅ Committed '{key}' to Redis.")
        else: # JSON backend
            # Update the long-term cache and then save it
            self._long_term_data_cache[key] = value
            self._save_long_term_data()
            print(f"✅ Committed '{key}' to {self.long_term_memory_path.name}.")

    def retrieve(self, key: str):
        """Retrieves a specific value directly from long-term memory."""
        if self.redis_client:
            value = self.redis_client.hget(self.long_term_memory_key, key)
            # Return a more consistent "not found" message if key doesn't exist
            return json.loads(value) if value is not None else f"I don't have a memory for '{key}' in Redis."
        else: # JSON backend
            return self._long_term_data_cache.get(key, f"I don't have a memory for '{key}' in JSON cache.")

    def _save_long_term_data(self):
        """Saves the _long_term_data_cache to the long-term backend (for JSON)."""
        if self.redis_client:
            # In Redis, 'commit' saves individual keys, this can be a no-op or save all session keys.
            # For simplicity, we'll let `commit` handle Redis persistence.
            pass
        else: # JSON backend
            content = json.dumps(self._long_term_data_cache, indent=2)
            self.long_term_memory_path.write_text(content, encoding='utf-8')

    def save_checkpoint(self, name: str) -> bool:
        """Saves the current session_memory to a named checkpoint."""
        # <<< FIX: A more permissive check that allows for underscores and hyphens
        # Create a clean version of the name for the check
        validation_name = name.replace('_', '').replace('-', '')
        if not validation_name.isalnum():
            print("❌ Checkpoint name must be alphanumeric, but can contain '_' and '-'.")
            return False

        # <<< NEW: Check for Redis backend
        if self.redis_client:
            print(f"🌀 Saving checkpoint '{name}' to Redis...")
            try:
                content = json.dumps(self.session_memory)
                self.redis_client.hset("giblet:checkpoints", name, content)
                print("✅ Shared checkpoint saved successfully.")
                return True
            except Exception as e:
                print(f"❌ Could not save checkpoint to Redis: {e}")
                return False

        # Fallback to file-based checkpoints
        if self._checkpoint_directory is None:
            self._checkpoint_directory = Path(__file__).parent.parent / "data/checkpoints"
        checkpoint_dir = self._checkpoint_directory
        checkpoint_dir.mkdir(exist_ok=True)
        checkpoint_file = checkpoint_dir / f"{name}.vibe"

        print(f"🌀 Saving checkpoint '{name}' to {checkpoint_file}...")
        try:
            content = json.dumps(self.session_memory, indent=2)
            checkpoint_file.write_text(content, encoding='utf-8')
            print("✅ Local checkpoint saved successfully.")
            return True
        except Exception as e:
            print(f"❌ Could not save local checkpoint: {e}")
            return False

    def load_checkpoint(self, name: str) -> bool:
        """Loads a named checkpoint into the current session_memory."""
        # <<< NEW: Check for Redis backend
        if self.redis_client:
            print(f"🌀 Loading checkpoint '{name}' from Redis...")
            try:
                content = self.redis_client.hget("giblet:checkpoints", name)
                if content is None:
                    print(f"❌ Shared checkpoint '{name}' not found.")
                    return False

                loaded_data = json.loads(content)
                self.session_memory.clear()
                self.session_memory.update(loaded_data)
                print("✅ Shared checkpoint loaded successfully into session memory.")
                return True
            except Exception as e:
                print(f"❌ Could not load checkpoint from Redis: {e}")
                return False

        # Fallback to file-based checkpoints
        if self._checkpoint_directory is None:
            self._checkpoint_directory = Path(__file__).parent.parent / "data/checkpoints"
        checkpoint_file = self._checkpoint_directory / f"{name}.vibe"
        if not checkpoint_file.exists():
            print(f"❌ Local checkpoint '{name}' not found.")
            return False

        print(f"🌀 Loading local checkpoint '{name}' from {checkpoint_file}...")
        try:
            content = checkpoint_file.read_text(encoding='utf-8')
            loaded_data = json.loads(content)
            self.session_memory.clear()
            self.session_memory.update(loaded_data)
            print("✅ Local checkpoint loaded successfully into session memory.")
            return True
        except Exception as e:
            print(f"❌ Could not load local checkpoint: {e}")
            return False
        
    def append_to_log(self, log_key: str, entry: dict, max_log_entries: int = 1000):
        """
        Appends an entry to a list stored under log_key in long-term memory.
        Manages log size by keeping only the most recent entries.
        """
        log_data = self.retrieve(log_key)
        if not isinstance(log_data, list):
            log_data = []
        
        log_data.append(entry)
        
        # Keep the log from growing indefinitely
        if len(log_data) > max_log_entries:
            log_data = log_data[-max_log_entries:]
        self.commit(log_key, log_data)