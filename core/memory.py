# core/memory.py
import json
import os
from pathlib import Path

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class Memory:
    def __init__(self):
        """
        Initializes the Memory module, connecting to Redis if configured,
        otherwise falling back to local JSON files.
        """
        self.backend_type = os.getenv("GIBLET_MEMORY_BACKEND", "json").lower()
        self.redis_client = None

        # --- Session Memory (volatile) ---
        self.session_memory = {}

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
            self.long_term_memory_path = Path(__file__).parent.parent / "data/memory.json"
            self.long_term_memory_path.touch(exist_ok=True)
            print("🧠 Memory module initialized with local JSON backend.")

        self.load_from_disk()

    def load_from_disk(self):
        """Loads the long-term memory from the configured backend."""
        if self.redis_client:
            # In Redis, data is "live", but we can log that we're ready.
            print("   (Redis backend is live, no initial load needed)")
        else: # JSON backend
            try:
                content = self.long_term_memory_path.read_text(encoding='utf-8')
                if content:
                    self.session_memory.update(json.loads(content))
            except (json.JSONDecodeError, FileNotFoundError):
                self.session_memory.update({})

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
            # For JSON, 'commit' just saves the whole session
            self.save_to_disk()
            print(f"✅ Committed '{key}' to {self.long_term_memory_path.name}.")

    def retrieve(self, key: str):
        """Retrieves a specific value directly from long-term memory."""
        if self.redis_client:
            value = self.redis_client.hget(self.long_term_memory_key, key)
            return json.loads(value) if value else None
        else: # JSON backend
            # For JSON, long-term is the same as session for this simple model
            return self.recall(key)

    def save_to_disk(self):
        """Saves the entire session memory to the long-term backend (for JSON)."""
        if self.redis_client:
            # In Redis, 'commit' saves individual keys, this can be a no-op or save all session keys.
            # For simplicity, we'll let `commit` handle Redis persistence.
            pass
        else: # JSON backend
            content = json.dumps(self.session_memory, indent=2)
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
        checkpoint_dir = Path(__file__).parent.parent / "data/checkpoints"
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
        checkpoint_file = Path(__file__).parent.parent / f"data/checkpoints/{name}.vibe"
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