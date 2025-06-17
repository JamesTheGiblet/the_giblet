# ui/cli.py
import logging
import subprocess
import sys
import webbrowser
import time
from pathlib import Path

# --- Core Module Imports ---
from core import utils
from core.memory import Memory
from core.roadmap_manager import RoadmapManager
from core.idea_synth import IdeaSynthesizer
from core.automator import Automator
from core.git_analyzer import GitAnalyzer
from core.code_generator import CodeGenerator
from core.command_manager import CommandManager
from core.plugin_manager import PluginManager

def start_cli_loop():
    """Starts the main interactive loop for The Giblet."""
    # --- Initialization ---
    memory = Memory()
    roadmap_manager = RoadmapManager(memory_system=memory)
    idea_synth = IdeaSynthesizer()
    automator = Automator()
    git_analyzer = GitAnalyzer()
    code_generator = CodeGenerator()
    command_manager = CommandManager()
    plugin_manager = PluginManager()
    
    # --- Register All Commands ---
    def register(name, handler, description=""):
        command_manager.register(name, handler, description)

    # Help Command
    def handle_help(args):
        print("\n--- The Giblet CLI: Help ---")
        for name, data in sorted(command_manager.commands.items()):
            print(f"  {name:<30} - {data['description']}")
        print("----------------------------\n")
    register("help", handle_help, "Shows this help message.")

    # File Commands
    register("read", lambda args: utils.read_file(args[0]) if args else print("Usage: read <filepath>"), "Reads a file.")
    register("write", lambda args: utils.write_file(args[0], input("Enter content (EOF to end):\n").rsplit('\nEOF')[0]) if args else print("Usage: write <filepath>"), "Writes to a file.")
    register("ls", lambda args: print('\n'.join(utils.list_files(args[0] if args else "."))), "Lists files.")
    register("exec", lambda args: print(utils.execute_command(" ".join(args))), "Executes a shell command.")
    
    # Memory Commands
    register("remember", lambda args: memory.remember(args[0], " ".join(args[1:])) if len(args) > 1 else print("Usage: remember <key> <value>"), "Saves to session memory.")
    register("recall", lambda args: print(memory.recall(args[0])) if args else print("Usage: recall <key>"), "Recalls from session memory.")
    register("commit", lambda args: memory.commit(args[0], " ".join(args[1:])) if len(args) > 1 else print("Usage: commit <key> <value>"), "Saves to long-term memory.")
    register("retrieve", lambda args: print(memory.retrieve(args[0])) if args else print("Usage: retrieve <key>"), "Retrieves from long-term memory.")

    # Workflow Commands
    register("checkpoint", lambda args: memory.save_checkpoint(args[1]) if len(args) > 1 and args[0] == 'save' else (memory.load_checkpoint(args[1]) if len(args) > 1 and args[0] == 'load' else print("Usage: checkpoint [save|load] <name>")), "Saves or loads a session checkpoint.")
    register("focus", lambda args: memory.remember("current_focus", None) or print("Focus cleared.") if args and args[0] == '--clear' else (memory.remember("current_focus", " ".join(args)) or print(f"Focus set to: {' '.join(args)}")) if args else print(f"Current focus: {memory.recall('current_focus')}"), "Sets or clears the session focus.")

    # Project & Git Commands
    register("roadmap", lambda args: roadmap_manager.complete_task(args[1]) if len(args) > 1 and args[0] == 'done' else roadmap_manager.view_roadmap(), "Views or updates the project roadmap.")
    register("git", lambda args: (print(git_analyzer.get_branch_status()) if args[0] == 'status' else print('\n'.join(git_analyzer.list_branches())) if args[0] == 'branches' else print('\n'.join(str(c) for c in git_analyzer.get_commit_log())) if args[0] == 'log' else print(git_analyzer.summarize_recent_activity(idea_synth)) if args[0] == 'summary' else print("Usage: git [status|branches|log|summary]")), "Interacts with the Git repository.")

    # Generation Commands
    register("idea", lambda args: print(idea_synth.generate_ideas(" ".join(args[1:]), weird_mode=True)) if args and args[0] == '--weird' else print(idea_synth.generate_ideas(" ".join(args))), "Brainstorms ideas using an LLM.")
    
    def handle_generate(args):
        if not args:
            print("Usage: generate [function|tests] <prompt_or_filepath>")
            return
        
        gen_type = args[0]
        prompt_or_path = " ".join(args[1:])

        if gen_type == "function":
            print("Please wait while The Giblet generates the code...")
            generated_code = code_generator.generate_function(prompt_or_path)
            print("\n--- Generated Code ---\n" + generated_code + "\n----------------------\n")
        elif gen_type == "tests":
            source_code = utils.read_file(prompt_or_path)
            if source_code:
                print("Please wait while The Giblet generates tests...")
                generated_tests = code_generator.generate_unit_tests(source_code, prompt_or_path)
                test_filename = f"tests/test_generated_for_{Path(prompt_or_path).stem}.py"
                Path("tests").mkdir(exist_ok=True) # Ensure tests directory exists
                utils.write_file(test_filename, generated_tests)
                print(f"\n✅ Successfully generated tests. Saved to '{test_filename}'")
                print(f"   To run them, exit The Giblet and use the command: pytest")
        else:
            print(f"Unknown generate command: '{gen_type}'. Try 'function' or 'tests'.")
    register("generate", handle_generate, "Generates code or tests.")
    register("build", lambda args: utils.write_file(f"ui_for_{Path(args[1]).stem}.py", code_generator.generate_streamlit_ui(utils.read_file(args[1]), args[1])) if len(args) > 1 and args[0] == 'ui' else print("Usage: build ui <filepath>"), "Builds a UI from a data model.")
    register("refactor", lambda args: utils.write_file(args[0], code_generator.refactor_code(utils.read_file(args[0]), args[1])) if len(args) > 1 and 'y' == input("Overwrite? (y/n): ").lower() else print("Refactor cancelled."), "Refactors a file based on an instruction.")

    # System Commands
    def handle_dashboard(args):
        print("🚀 Launching The Giblet Dashboard...")
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.runOnSave", "true"])
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
    register("dashboard", handle_dashboard, "Launches the web-based visual dashboard.")

    # --- Load Plugins ---
    plugin_manager.discover_plugins()
    for plugin in plugin_manager.plugins:
        plugin.register_commands(command_manager)

    print("🧠 The Giblet is awake. All commands registered. Type 'help' for a list of commands.")
    
    while True:
        try:
            # Dynamic prompt logic...
            current_focus = memory.recall("current_focus")
            prompt = f" giblet [focus: {current_focus[:20]}...]>" if current_focus else f" giblet [branch: {git_analyzer.repo.active_branch.name}]>" if git_analyzer.repo else " giblet> "
            
            user_input = input(prompt).strip()
            if not user_input: continue

            # Simplified parsing
            parts = user_input.split(" ", 1)
            command_name = parts[0].lower()
            # Handle multi-word commands like 'roadmap done'
            if len(parts) > 1 and f"{command_name} {parts[1].split()[0]}" in command_manager.commands:
                command_name = f"{command_name} {parts[1].split()[0]}"
                args = parts[1].split()[1:]
            else:
                args = parts[1].split() if len(parts) > 1 else []
            
            command_manager.execute(command_name, args)

        except KeyboardInterrupt:
            print("\n🧠 Going to sleep. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            logging.exception("An unhandled exception occurred in the CLI loop.")