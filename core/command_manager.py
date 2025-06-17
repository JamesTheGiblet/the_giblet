# core/command_manager.py
class CommandManager:
    def __init__(self):
        self.commands = {}
        print("📦 Command Manager initialized.")

    def register(self, name: str, handler, description: str):
        """Registers a command and its handler function."""
        self.commands[name] = {"handler": handler, "description": description}

    def execute(self, command_name: str, args: list):
        """Executes a registered command."""
        if command_name in self.commands:
            # Call the handler with the list of arguments
            self.commands[command_name]["handler"](args)
        else:
            print(f"Unknown command: '{command_name}'. Type 'help' for options.")