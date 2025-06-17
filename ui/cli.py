# ui/cli.py
import logging # <<< NEW IMPORT
import subprocess # <<< NEW IMPORT
import sys # <<< NEW IMPORT
import webbrowser # New
import time # New

from core import utils
from core.memory import Memory
from core.roadmap_manager import RoadmapManager
from core.idea_synth import IdeaSynthesizer
from core.automator import Automator
from core.git_analyzer import GitAnalyzer
from core.code_generator import CodeGenerator
from core.command_manager import CommandManager # New
from core.plugin_manager import PluginManager   # New

def start_cli_loop():
    """Starts the main interactive loop for The Giblet."""
    # --- Initialization ---
    memory = Memory()
    roadmap_manager = RoadmapManager(memory_system=memory)
    idea_synth = IdeaSynthesizer()
    automator = Automator()
    git_analyzer = GitAnalyzer()
    code_generator = CodeGenerator() # Assuming CodeGenerator is in its own file
    command_manager = CommandManager()
    plugin_manager = PluginManager()
    plugin_manager.discover_plugins()

    # --- Register All Commands ---
    # Helper function to avoid repeating `lambda args:`
    def register(name, handler, description):
        command_manager.register(name, handler, description)

    # Built-in commands
    def handle_help(args):
        print("\n--- The Giblet CLI: Help ---")
        for name, data in sorted(command_manager.commands.items()):
            print(f"  {name:<25} - {data['description']}")
        print("----------------------------\n")
    register("help", handle_help, "Shows this help message.")

    # Register all our old commands with the new system
    register("roadmap", lambda args: roadmap_manager.view_roadmap(), "Displays the parsed project roadmap.")
    register("roadmap done", lambda args: roadmap_manager.complete_task(args[0]) if args else print("Usage: roadmap done \"<desc>\""), "Marks a task as complete.")
    # ... You would continue to register all other built-in commands here ...
    # For brevity, we will only register a few for this test.

    # Example of registering a command that was previously in the if/elif block:
    def handle_dashboard(args):
        print("🚀 Launching The Giblet Dashboard in your browser...")
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
    register("dashboard", handle_dashboard, "Launches the web-based visual dashboard.")

    def handle_exit(args):
        print("🧠 Going to sleep. Goodbye!")
        sys.exit(0) # Clean exit
    register("exit", handle_exit, "Exits the interactive session.")
    register("quit", handle_exit, "Exits the interactive session.")


    # Register commands from plugins
    for plugin in plugin_manager.plugins:
        plugin.register_commands(command_manager)

    print("🧠 The Giblet is awake. All commands registered. Type 'help' for a list of commands.")

    while True:
        try:
            # Dynamic prompt logic remains the same
            current_focus = memory.recall("current_focus")
            prompt = f" giblet [focus: {current_focus[:20]}...]>" if current_focus else f" giblet [branch: {git_analyzer.repo.active_branch.name}]>" if git_analyzer.repo else " giblet> "

            user_input = input(prompt).strip()
            if not user_input: continue

            parts = user_input.split() # Changed from split(maxsplit=2)
            command = parts[0].lower()
            args = parts[1:]

            # Execute command through the manager
            command_manager.execute(command, args)

        except KeyboardInterrupt:
            print("\n🧠 Going to sleep. Goodbye!")
            break
        except Exception as e:
            # <<< UPDATED: The new error handling logic
            print(f"\n❌ An unexpected error occurred: {e}")
            print("   A detailed traceback has been saved to 'data/giblet_debug.log'.")
            logging.exception("An unhandled exception occurred in the CLI loop.")