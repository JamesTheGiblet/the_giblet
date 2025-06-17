# core/command_manager.py
class CommandManager:
    def __init__(self):
        self.commands = {}
        print("📦 Command Manager initialized.")

    def register(self, name: str, handler, description: str):
        """Registers a command and its handler function."""
        self.commands[name] = {"handler": handler, "description": description}

    def execute(self, command_name: str, args: list):
        if command_name in self.commands:
            return self.commands[command_name]["handler"](args) # ADDED return
        else:
            print(f"Unknown command: '{command_name}'. Type 'help' for options.")
            return None # Or handle error appropriately
