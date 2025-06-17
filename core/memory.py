# core/memory.py
import json
from pathlib import Path

# Define the path to our persistent memory file
MEMORY_FILE = Path(__file__).parent.parent / "data/memory.json"

class Memory:
    def __init__(self):
        """
        Initializes the memory system, loading persistent data if it exists.
        """
        self.session_memory = {}  # For short-term, session-only data
        self.long_term_memory = self._load_from_disk()
        print("🧠 Memory module initialized.")

    def _load_from_disk(self) -> dict:
        """Loads the long-term memory from the JSON file."""
        # Check if the file exists before trying to read it
        if MEMORY_FILE.exists():
            # <<< FIX: Read content first, then check if it's empty
            content = MEMORY_FILE.read_text(encoding='utf-8')
            if content:
                print(f"🧠 Loading long-term memory from {MEMORY_FILE}")
                return json.loads(content)
        
        # <<< FIX: This line will now be reached if the file doesn't exist OR is empty
        print("🧠 No long-term memory file found or file is empty. Starting fresh.")
        return {"roadmap": [], "bug_archive": [], "preferences": {}}

    def save_to_disk(self):
        """Saves the current long-term memory to the JSON file."""
        print(f"🧠 Saving long-term memory to {MEMORY_FILE}")
        try:
            MEMORY_FILE.write_text(json.dumps(self.long_term_memory, indent=2), encoding='utf-8')
            return True
        except Exception as e:
            print(f"❌ Could not save memory file: {e}")
            return False

    def save_checkpoint(self, name: str) -> bool:
        """Saves the current session_memory to a named checkpoint file."""
        if not name.isalnum():
            print("❌ Checkpoint name must be alphanumeric.")
            return False
        
        checkpoint_dir = Path(__file__).parent.parent / "data/checkpoints"
        checkpoint_dir.mkdir(exist_ok=True) # Ensure directory exists
        checkpoint_file = checkpoint_dir / f"{name}.vibe"

        print(f"🌀 Saving checkpoint '{name}' to {checkpoint_file}...")
        try:
            content = json.dumps(self.session_memory, indent=2)
            checkpoint_file.write_text(content, encoding='utf-8')
            print("✅ Checkpoint saved successfully.")
            return True
        except Exception as e:
            print(f"❌ Could not save checkpoint: {e}")
            return False

    def load_checkpoint(self, name: str) -> bool:
        """Loads a named checkpoint file into the current session_memory."""
        checkpoint_file = Path(__file__).parent.parent / f"data/checkpoints/{name}.vibe"
        
        if not checkpoint_file.exists():
            print(f"❌ Checkpoint '{name}' not found.")
            return False
            
        print(f"🌀 Loading checkpoint '{name}' from {checkpoint_file}...")
        try:
            content = checkpoint_file.read_text(encoding='utf-8')
            loaded_data = json.loads(content)
            self.session_memory.clear() # Clear old session data
            self.session_memory.update(loaded_data) # Load in the new data
            print("✅ Checkpoint loaded successfully into session memory.")
            return True
        except Exception as e:
            print(f"❌ Could not load checkpoint: {e}")
            return False
        
    # --- Session Memory Methods ---
    def remember(self, key: str, value):
        """Saves a key-value pair to session memory."""
        self.session_memory[key] = value

    def recall(self, key: str, default=None):
        """Retrieves a value from session memory."""
        return self.session_memory.get(key, default)

    # --- Long-Term Memory Methods ---
    def commit(self, key: str, value):
        """Saves a key-value pair to long-term memory and persists it."""
        self.long_term_memory[key] = value
        self.save_to_disk()

    def retrieve(self, key: str, default=None):
        """Retrieves a value from long-term memory."""
        return self.long_term_memory.get(key, default)