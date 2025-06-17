# core/command_manager.py
from datetime import datetime

class CommandManager:
    def __init__(self, memory_system=None): # Add memory_system, make it optional for now for backward compatibility if needed
        self.commands = {}
        self.memory = memory_system
        self.COMMAND_LOG_KEY = "giblet_command_log_v1"
        print("📦 Command Manager initialized.")

    def register(self, name: str, handler, description: str):
        """Registers a command and its handler function."""
        self.commands[name] = {"handler": handler, "description": description}

    def execute(self, command_name: str, args: list):
        if command_name in self.commands:
            if self.memory:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "command": command_name,
                    "args": args,
                    # "session_id": self.memory.get_session_id() # Future: if you implement session IDs
                }
                self.memory.append_to_log(self.COMMAND_LOG_KEY, log_entry)

            return self.commands[command_name]["handler"](args) # ADDED return
        else:
            print(f"Unknown command: '{command_name}'. Type 'help' for options.")
            return None # Or handle error appropriately
