# core/command_manager.py
from datetime import datetime
from typing import TYPE_CHECKING # For forward reference
if TYPE_CHECKING:
    from core.skill_manager import Skill # Import for type hinting

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

    def register_skill_command(self, skill_instance: 'Skill'): # Forward reference Skill
        """Registers a command that will be handled by a skill."""
        if not skill_instance or not hasattr(skill_instance, 'NAME') or not skill_instance.NAME:
            print("⚠️ Attempted to register an invalid skill instance.")
            return

        skill_name = skill_instance.NAME
        skill_description = getattr(skill_instance, 'DESCRIPTION', "No description provided for this skill.")

        def skill_handler(args: list[str]) -> bool:
            # Parse args into a dictionary for the skill's **params
            # This is a simple parser; more robust parsing might be needed
            params_dict = {}
            for arg in args:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    params_dict[key] = value
                else:
                    # Handle positional arguments or flags if your skills need them
                    # For now, we'll assume key=value or ignore
                    pass
            
            # Context for the skill - this might come from memory or elsewhere
            context = {"current_focus": self.memory.recall("current_focus") if self.memory and hasattr(self.memory, 'recall') else None}
            # Goal description for the skill - this might be more complex
            goal_description = f"Execute skill {skill_name}"

            print(f"Executing skill: {skill_name} with params: {params_dict}")
            return skill_instance.execute(goal_description, context, **params_dict)

        self.register(skill_name, skill_handler, skill_description)
        print(f"📦 Skill command '{skill_name}' registered.")
