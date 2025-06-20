# ui/cli.py
import json
import logging
import subprocess
import sys
import webbrowser
import time
from pathlib import Path
import shlex # <<< NEW IMPORT
import httpx # <<< NEW IMPORT

# --- Core Module Imports ---
from core import roadmap_manager, utils
from core.memory import Memory
from core.idea_synth import IdeaSynthesizer
from core.automator import Automator
from core.git_analyzer import GitAnalyzer
from core.code_generator import CodeGenerator
from core.command_manager import CommandManager
from core.plugin_manager import PluginManager
from core.watcher import start_watching # 1. Add the new import at the top
from core.agent import Agent # 1. Add the new import
from core.user_profile import DEFAULT_PROFILE_STRUCTURE, UserProfile # New import for UserProfile
from core.skill_manager import SKILLS_DIR, SkillManager # New import for SkillManager
from core.pattern_analyzer import PatternAnalyzer # New import
from core.llm_provider_base import LLMProvider # Import base provider
from core.capability_assessor import CapabilityAssessor # New import for Gauntlet
from core.llm_providers import GeminiProvider, OllamaProvider # Import specific providers
from core.style_preference import StylePreferenceManager # Import StylePreferenceManager
from core.genesis_logger import GenesisLogger # Import GenesisLogger
from core.project_contextualizer import ProjectContextualizer
from core.idea_interpreter import IdeaInterpreter # Import IdeaInterpreter
from core.mini_readme_generator import MiniReadmeGenerator # 1. Add the new import at the top
from core.readme_generator import ReadmeGenerator 
from core.roadmap_generator import RoadmapGenerator # <<< 1. IMPORT

# --- Proactive Learner Import (now uses actual UserProfile) ---
try:
    from core.proactive_learner import ProactiveLearner
except ImportError as e:
    print(f"Warning: ProactiveLearner module could not be loaded: {e}. Proactive suggestion features will be limited.")
    # Fallback for ProactiveLearner and UserProfilePlaceholder
    class ProactiveLearner: pass
    class UserProfilePlaceholder: pass

def start_cli_loop():
    """Starts the main interactive loop for The Giblet."""
    # --- Initialization ---
    memory = Memory() # Memory first
    user_profile = UserProfile(memory_system=memory) # UserProfile needs memory
    style_manager_for_cli = StylePreferenceManager() # Instantiate StylePreferenceManager
    genesis_logger_cli = GenesisLogger() # Instantiate GenesisLogger

    # Helper function to get the configured LLM provider for CLI
    def get_cli_llm_provider(profile: UserProfile) -> LLMProvider | None:
        active_provider_name = profile.get_preference("llm_provider_config", "active_provider", "gemini")
        raw_provider_configs = profile.get_preference("llm_provider_config", "providers")

        provider_configs = {}
        if isinstance(raw_provider_configs, dict):
            provider_configs = raw_provider_configs
        elif isinstance(raw_provider_configs, str) and raw_provider_configs.startswith("{") and raw_provider_configs.endswith("}"): # Basic check for JSON string
            try:
                provider_configs = json.loads(raw_provider_configs) # Attempt to parse if it's a stringified JSON
            except json.JSONDecodeError:
                print(f"⚠️ CLI: Could not parse 'providers' config string from profile. Using defaults. String was: {raw_provider_configs}")
                provider_configs = DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]
        else: # Not a dict, not a parsable string, or None
            print(f"⚠️ CLI: 'providers' config in profile is not a valid dictionary. Using defaults. Value was: {raw_provider_configs}")
            provider_configs = DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"] # Fallback to default structure

        if active_provider_name == "gemini":
            gemini_config = provider_configs.get("gemini", {})
            api_key = gemini_config.get("api_key")
            model_name = gemini_config.get("model_name", "gemini-1.5-flash-latest")
            print(f"CLI: Configuring GeminiProvider (model: {model_name}, API key from profile: {'yes' if api_key else 'no/use .env'})")
            return GeminiProvider(model_name=model_name, api_key=api_key if api_key else None)
        elif active_provider_name == "ollama":
            ollama_config = provider_configs.get("ollama", {})
            base_url = ollama_config.get("base_url", "http://localhost:11434")
            model_name = ollama_config.get("model_name", "mistral")
            print(f"CLI: Configuring OllamaProvider (model: {model_name}, url: {base_url})")
            return OllamaProvider(model_name=model_name, base_url=base_url)
        else:
            print(f"⚠️ CLI: Unknown LLM provider '{active_provider_name}' configured. Defaulting to Gemini.")
            return GeminiProvider()

    cli_llm_provider = get_cli_llm_provider(user_profile)

    if not cli_llm_provider or not cli_llm_provider.is_available():
        print(f"⚠️ CLI: Configured LLM provider ({cli_llm_provider.PROVIDER_NAME if cli_llm_provider else 'N/A'}) is not available. LLM features may be limited.")
        # CLI might be more tolerant or simply print warnings, as it's interactive.

    # Instantiate RoadmapManager for local 'todo' commands
    # The main 'roadmap' command now uses the API, but 'todo' might still use local logic.
    roadmap_manager_cli = roadmap_manager.RoadmapManager(memory_system=memory, style_preference_manager=style_manager_for_cli)

    automator = Automator()
    git_analyzer = GitAnalyzer()
    command_manager = CommandManager()

    # Instantiate ProjectContextualizer - assumes CLI runs from project root or similar
    # The memory instance is already created.
    project_contextualizer_cli = ProjectContextualizer(memory_system=memory, project_root=".") # Added project_root

    # Update instantiations to include project_contextualizer
    idea_synth = IdeaSynthesizer(user_profile=user_profile, memory_system=memory, llm_provider=cli_llm_provider,
                                 project_contextualizer=project_contextualizer_cli,
                                 style_preference_manager=style_manager_for_cli)
    code_generator = CodeGenerator(user_profile=user_profile, memory_system=memory, llm_provider=cli_llm_provider, project_contextualizer=project_contextualizer_cli)
    mini_readme_generator_cli = MiniReadmeGenerator(
        llm_provider=cli_llm_provider,
        style_manager=style_manager_for_cli,
        user_profile=user_profile
    )
    # <<< 2. INSTANTIATE THE ROADMAP GENERATOR
    readme_generator_cli = ReadmeGenerator(
        llm_provider=cli_llm_provider,
        style_manager=style_manager_for_cli
    )
    # Instantiate RoadmapGenerator for Genesis Mode document generation
    roadmap_generator_cli = RoadmapGenerator(
        llm_provider=cli_llm_provider,
        style_manager=style_manager_for_cli
    )

    # Instantiate IdeaInterpreter
    idea_interpreter_cli = IdeaInterpreter(
        llm_provider=cli_llm_provider,
        user_profile=user_profile,
        memory=memory, # Added missing argument
        style_manager=style_manager_for_cli,
        project_contextualizer=project_contextualizer_cli # Added missing argument
    )
    proactive_learner_instance = ProactiveLearner(user_profile=user_profile) if ProactiveLearner is not None else None

    skill_manager = SkillManager(user_profile=user_profile, memory=memory, command_manager_instance=command_manager) # Instantiate SkillManager
    agent = Agent(idea_synth=idea_synth, code_generator=code_generator, skill_manager=skill_manager) # Pass skill_manager
    pattern_analyzer = PatternAnalyzer(memory_system=memory) # Instantiate PatternAnalyzer
    plugin_manager = PluginManager()
    MAX_FIX_ATTEMPTS = 3 # Define how many times to attempt self-correction
    
    # --- Register All Commands ---
    def register(name, handler, description=""):
        command_manager.register(name, handler, description)

    # --- Helper function for the Genesis interview loop ---
    def _run_genesis_interview(initial_idea: str, idea_interpreter, mem):
        """
        Handles the common logic for the interactive Q&A session in Genesis mode.
        """
        print(f"\n🚀 Starting Genesis Mode for idea: \"{initial_idea}\"")
        
        questions = idea_interpreter.start_interpretation_session(initial_idea)
        if not questions:
            print("\n❌ Error: Could not start the interpretation session. The LLM might be unavailable.")
            return

        print("\n🤖 The Giblet asks:\n")
        print(questions)
        
        print("\n> Provide your answers below. Type 'EOF' or press Ctrl+D on a new line when you're done.")
        user_answers_lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "EOF":
                    break
            except EOFError:
                break
            user_answers_lines.append(line)
        user_answers = "\n".join(user_answers_lines)

        if not user_answers.strip():
            print("\n❌ No answer provided. Aborting Genesis session.")
            return

        print("\nAnalyzing and synthesizing project brief...")
        result = idea_interpreter.submit_answer_and_continue(user_answers)

        if result.get("status") == "complete":
            final_brief = result.get("data", {})
            mem.remember("last_genesis_brief", final_brief)
            print("\n--- ✅ Genesis Complete: Synthesized Project Brief ---")
            print(json.dumps(final_brief, indent=2))
            print("----------------------------------------------------\n")
            print("Next step: Run `genesis generate-readme` or `genesis scaffold`.")
        else:
            print(f"\n❌ An error occurred during synthesis: {result.get('message', 'Unknown error.')}")

    # Help Command
    def handle_help(args):
        print("\n--- The Giblet CLI: Help ---")
        for name, data in sorted(command_manager.commands.items()):
            print(f"  {name:<30} - {data['description']}") # Ensure consistent spacing
        print("----------------------------\n")
        print("Agent Commands:")
        print("  plan \"<goal>\"             - Creates a multi-step plan to achieve a goal.")
        print("  execute                    - Executes the most recently created plan.")
        print("\nUser Profile Commands:")
        print("  profile get [<cat> [<key>]] - Gets a profile value or the whole profile.")
        print("  profile set <cat> <key> <val> - Sets a profile value.")
        print("  profile clear              - Clears the entire user profile.")
        print("\nLLM Configuration Commands:")
        print("  genesis start \"<idea>\"     - Begins the Genesis Mode idea interpretation.") # New help line
        print("  gauntlet edit              - Opens the Gauntlet Test Editor UI.") # New help line
        print("  assess model               - Runs capability tests on the current LLM.") # New help line
        print("  llm status                 - Shows current LLM provider and model.")
        print("  llm use <gemini|ollama>    - Sets the active LLM provider.")
        print("  llm config <provider> <key> <value> - Configure provider-specific settings (e.g., model_name, api_key, base_url).")
        print("  feedback <rating> [comment] - Provide feedback on the last AI output (rating: good, bad, ok).")
        print("\nSkill Commands:")
        print("  skills list                - Lists available skills.")
        print("  skills refresh             - Re-scans the skills directory.")
        print("  skills create_from_plan <SkillName> [\"trigger phrase\"] - Generates a new skill from the last executed plan.")
        print("\nHistory Commands:")
        print("  learn suggestions          - Analyzes feedback & profile for proactive suggestions.") # New help line
        print("  history analyze_patterns   - Analyzes command history for potential skill candidates.")
        print("  history commands [limit]   - Shows recent command history (default limit 10).")
    register("help", handle_help, "Shows this help message.")

    # File Commands
    def handle_write(args):
        if not args:
            print("Usage: write <filepath>")
            return
        filepath = args[0]
        print("Enter content for the file. Type 'EOF' on a new line to finish.")
        lines = []
        while True:
            try:
                line = input()
                if line == "EOF":
                    break
                lines.append(line)
            except EOFError: # Handles Ctrl+D as EOF
                break
        content = "\n".join(lines)
        if utils.write_file(filepath, content):
            memory.remember('last_file_written', filepath) # Store for the agent
            print(f"✅ Content written to {filepath}")
        else:
            print(f"❌ Failed to write to {filepath}")

    register("read", lambda args: utils.read_file(args[0]) if args else print("Usage: read <filepath>"), "Reads a file.")
    register("write", handle_write, "Writes content to a file.")
    register("ls", lambda args: print('\n'.join(utils.list_files(args[0] if args else "."))), "Lists files.")
    register("exec", lambda args: utils.execute_command(" ".join(args)), "Executes a shell command.")
    
    # Memory Commands
    register("remember", lambda args: memory.remember(args[0], " ".join(args[1:])) if len(args) > 1 else print("Usage: remember <key> <value>"), "Saves to session memory.")
    register("recall", lambda args: print(memory.recall(args[0])) if args else print("Usage: recall <key>"), "Recalls from session memory.")
    register("commit", lambda args: memory.commit(args[0], " ".join(args[1:])) if len(args) > 1 else print("Usage: commit <key> <value>"), "Saves to long-term memory.")
    register("retrieve", lambda args: print(memory.retrieve(args[0])) if args else print("Usage: retrieve <key>"), "Retrieves from long-term memory.")

    # Workflow Commands
    register("checkpoint", lambda args: memory.save_checkpoint(args[1]) if len(args) > 1 and args[0] == 'save' else (memory.load_checkpoint(args[1]) if len(args) > 1 and args[0] == 'load' else print("Usage: checkpoint [save|load] <name>")), "Saves or loads a session checkpoint.")
    register("focus", lambda args: memory.remember("current_focus", None) or print("Focus cleared.") if args and args[0] == '--clear' else (memory.remember("current_focus", " ".join(args)) or print(f"Focus set to: {' '.join(args)}")) if args else print(f"Current focus: {memory.recall('current_focus')}"), "Sets or clears the session focus.")

    # Project & Git Commands
    def handle_roadmap(args):
        print("🗺️  Fetching roadmap from Giblet API...")
        try:
            response = httpx.get("http://localhost:8000/roadmap")
            response.raise_for_status() # Raises an exception for 4xx/5xx errors

            data = response.json()
            tasks = data.get("roadmap", [])

            if not tasks:
                print("No tasks found.")
                return

            print("\n--- Project Roadmap ---")
            for task in tasks:
                icon = "✅" if task["status"] == "complete" else "🚧"
                print(f" {icon} {task['description']}")
            print("-----------------------\n")

        except httpx.RequestError as e:
            print(f"❌ API Request Failed: Could not connect to the Giblet API at http://localhost:8000. Is the server running?")
        except Exception as e:
            print(f"❌ An error occurred: {e}")
    register("roadmap", handle_roadmap, "Views the project roadmap via the API.")
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

    # Collaboration Commands
    def handle_todo(args):
        if not args:
            print("Usage: todo [add|list]")
            return

        sub_command = args[0]
        if sub_command == "add":
            arg_string = " ".join(args[1:])
            try:
                parsed_args = shlex.split(arg_string)
                if len(parsed_args) != 2:
                    raise ValueError("Invalid number of arguments for 'todo add'")

                assignee, description = parsed_args

                if not assignee.startswith('@'):
                    raise ValueError("Assignee must start with '@'")
                roadmap_manager_cli.add_shared_task(description, assignee) 

            except ValueError as e:
                print(f"Error: {e}")
                print('Usage: todo add "@<user>" "<description>" (ensure description is quoted if it contains spaces)')
        elif sub_command == "list":
            tasks = roadmap_manager_cli.view_shared_tasks() 
            if tasks:
                print("\n--- Shared To-Do List ---")
                for task in tasks:
                    print(f"  - [{task.get('status', 'N/A').upper()}] {task.get('description', 'No description')} (Assigned to: {task.get('assignee', 'Unassigned')}, ID: {task.get('id', 'N/A')})")
                print("-------------------------\n")
            else:
                print("No shared tasks found.")
        else:
            print(f"Unknown todo command: '{sub_command}'. Try 'add' or 'list'.")
    register("todo", handle_todo, "Manages shared to-do list (add, list).")

    # System Commands
    def handle_dashboard(args):
        existing_process = memory.recall('streamlit_process')
        if existing_process and isinstance(existing_process, subprocess.Popen) and existing_process.poll() is None:
            print("Dashboard is already running. Opening a new browser tab to http://localhost:8501...")
            webbrowser.open("http://localhost:8501")
            return

        print("🚀 Launching The Giblet Dashboard...")
        print("   If a browser tab doesn't open, please navigate to http://localhost:8501")
        try:
            new_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "ui/dashboard.py", "--server.runOnSave", "true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            memory.remember('streamlit_process', new_process)
            time.sleep(3)
            webbrowser.open("http://localhost:8501")
        except Exception as e:
            print(f"❌ Failed to launch dashboard: {e}")
    register("dashboard", handle_dashboard, "Launches or focuses the web dashboard.")

    def handle_execute(args):
        plan = memory.recall('last_plan')
        if not isinstance(plan, list) or not plan:
            print("❌ No plan found in memory. Please generate a plan first using the 'plan' command.")
            if isinstance(plan, str): 
                print(f"   (Details: {plan})")
            return

        print("\n--- About to Execute Plan ---")
        for i, step in enumerate(plan, 1):
            print(f"Step {i}: giblet {step}")
        print("---------------------------\n")

        confirm = input("Proceed with execution? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Execution cancelled.")
            return

        print("\n🚀 Executing plan...")
        for i, command_string in enumerate(plan, 1):
            print(f"\n--- Running Step {i}: giblet {command_string} ---")
            parts = shlex.split(command_string)
            if not parts: 
                print(f"   └─ Skipping empty command in plan (Step {i}).")
                continue 

            command_name = parts[0].lower()
            cmd_args = parts[1:]
            execution_result = command_manager.execute(command_name, cmd_args)

            return_code, stdout, stderr = 0, "", "" 
            if isinstance(execution_result, tuple) and len(execution_result) == 3:
                return_code, stdout, stderr = execution_result
            
            is_test_step = (command_name == "exec" and cmd_args and "pytest" in " ".join(cmd_args))

            if is_test_step and return_code != 0:
                current_error_log = stdout + stderr
                current_return_code = return_code

                for attempt in range(MAX_FIX_ATTEMPTS):
                    print(f"   └─ ❗ Tests failed. Attempting self-correction ({attempt + 1}/{MAX_FIX_ATTEMPTS})...")
                    file_to_test = memory.recall('last_file_written')
                    if not file_to_test and len(cmd_args) > 0:
                        for arg_path in cmd_args: 
                            if Path(arg_path).is_file() and arg_path.endswith(".py"): 
                                file_to_test = arg_path
                                break
                            elif Path(arg_path).is_dir(): 
                                pass 

                    if file_to_test:
                        code_to_fix = utils.read_file(file_to_test)
                        if code_to_fix:
                            print(f"   └─ 🤖 LLM attempting to fix {file_to_test} based on error (first 300 chars):\n{current_error_log[:300]}...") 
                            fixed_code = agent.attempt_fix(code_to_fix, current_error_log)
                            print(f"   └─ Proposed fix by LLM for {file_to_test}:\n-------\n{fixed_code}\n-------")
                            
                            has_actual_code = any(line.strip() and not line.strip().startswith("#") for line in fixed_code.splitlines())
                            if fixed_code and has_actual_code:
                                utils.write_file(file_to_test, fixed_code)
                                print(f"   └─ ✨ Applied potential fix to {file_to_test}. Retrying tests...")
                                current_return_code, retry_stdout, retry_stderr = utils.execute_command(" ".join(cmd_args))
                                current_error_log = retry_stdout + retry_stderr 

                                if current_return_code == 0:
                                    print("   └─ ✅ Self-correction successful! Tests now pass.")
                                    break 
                                else:
                                    print(f"   └─ ❌ Self-correction attempt {attempt + 1} failed. Tests still failing.")
                                    if attempt + 1 == MAX_FIX_ATTEMPTS:
                                        print(f"      └─ Max fix attempts reached. Last error log:\n{current_error_log}")
                            else:
                                print(f"   └─ ⚠️ LLM did not provide a valid fix on attempt {attempt + 1}. Stopping self-correction for this step.")
                                break 
                        else:
                            print(f"   └─ ⚠️ Could not read file {file_to_test} to attempt fix. Stopping self-correction.")
                            break 
                    else:
                        print("   └─ ⚠️ Could not determine which file to fix for self-correction. Stopping.")
                        break 
                else: 
                    if current_return_code != 0: 
                        print("   └─ ❌ Self-correction ultimately failed after all attempts.")
                        
        print("\n✅ Plan execution complete.")

    register("plan", handle_plan, "Creates a multi-step plan to achieve a goal.")
    register("execute", handle_execute, "Executes the most recently created plan.")

    def handle_watch(args):
        start_watching()
    register("watch", handle_watch, "Enters watch mode to provide proactive suggestions on file changes.")

    def handle_plan(args):
        if not args:
            print("Usage: plan \"<your high-level goal>\"")
            return

        goal = " ".join(args)
        plan = agent.create_plan(goal)

        print("\n--- Generated Plan ---")
        if plan and not (isinstance(plan, list) and len(plan) > 0 and "Failed to generate" in plan[0]):
            memory.remember('last_plan', plan)
            for i, step in enumerate(plan, 1):
                print(f"Step {i}: giblet {step}")
            print("----------------------\n")
            print("To run this plan, use the 'execute' command.")
        elif isinstance(plan, list) and len(plan) > 0 :
            print(plan[0]) 
            print("----------------------\n")
        else:
            print("Failed to generate a plan or the plan was empty.")
            print("----------------------\n")

    # User Profile Commands
    def handle_profile(args):
        if not args:
            print("Usage: profile [get|set|clear] [<category> <key> <value>]")
            print("Current profile data:")
            print(user_profile.get_all_data())
            return

        action = args[0].lower()
        if action == "get":
            if len(args) == 1:
                print(user_profile.get_all_data())
            elif len(args) == 2: 
                category_name = args[1]
                category_data = user_profile.data.get(category_name) 
                if category_data is not None: 
                    if category_data: 
                        print(f"Preferences in category '{category_name}':")
                        for key, value_item in category_data.items(): 
                            print(f"  {key}: {value_item}")
                    else:
                        print(f"Category '{category_name}' is empty.")
                else:
                    print(f"Category '{category_name}' not found.")
            elif len(args) >= 3:
                value = user_profile.get_preference(args[1], args[2])
                print(f"{args[1]}.{args[2]} = {value if value is not None else 'Not set'}")
            else:
                print("Usage: profile get [<category> [<key>]]")
        elif action == "set":
            if len(args) >= 4:
                user_profile.add_preference(args[1], args[2], " ".join(args[3:]))
            else:
                print("Usage: profile set <category> <key> <value>")
        elif action == "clear":
            user_profile.clear_profile()
        else:
            print(f"Unknown profile action: {action}. Use 'get', 'set', or 'clear'.")
    register("profile", handle_profile, "Manages user profile settings.")

    # Gauntlet Editor Command
    def handle_gauntlet_edit(args):
        print("🚀 Launching Gauntlet Test Editor...")
        try:
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", "gauntlet_editor.py"])
            print("   Editor should open in your web browser. If not, ensure Streamlit is installed.")
        except Exception as e:
            print(f"❌ Failed to launch Gauntlet Editor: {e}")
    register("gauntlet edit", handle_gauntlet_edit, "Opens the interactive Gauntlet Test Editor.")

    # Capability Assessor Command
    def handle_assess_model(args):
        if not cli_llm_provider or not cli_llm_provider.is_available():
            print("❌ Cannot assess model: No LLM provider is available or configured correctly.")
            return

        print(f"Preparing to assess LLM: {cli_llm_provider.PROVIDER_NAME} - {cli_llm_provider.model_name}")
        assessor = CapabilityAssessor(llm_provider=cli_llm_provider, code_generator=code_generator, idea_synthesizer=idea_synth)
        capability_profile = assessor.run_gauntlet()

        print("\n--- LLM Capability Profile ---")
        print(json.dumps(capability_profile, indent=2))
        print("----------------------------\n")

        if capability_profile:
            provider_name = capability_profile.get("provider_name")
            model_name = capability_profile.get("model_name")
            if provider_name and model_name:
                user_profile.save_gauntlet_profile(provider_name, model_name, capability_profile)

    register("assess model", handle_assess_model, "Runs capability tests (gauntlet) on the current LLM.")

    # LLM Configuration Commands
    def handle_llm_config(args):
        if not args:
            print("Usage: llm <status|use|config> [options...]")
            print("Example: llm use ollama")
            print("Example: llm config gemini model_name gemini-pro")
            print("Example: llm config ollama base_url http://localhost:11435")
            return

        action = args[0].lower()
        if action == "status":
            active_provider_from_profile = user_profile.get_preference("llm_provider_config", "active_provider")
            effective_active_provider = active_provider_from_profile or "gemini" 
            
            print(f"Effective Active LLM Provider: {effective_active_provider}")
            if not active_provider_from_profile:
                print("  (Note: No active provider explicitly set in profile, defaulting to Gemini)")

            provider_configs = user_profile.get_preference("llm_provider_config", "providers", {})
            
            for provider_name_key in ["gemini", "ollama"]: 
                print(f"\nSettings for {provider_name_key.capitalize()}:")
                config = provider_configs.get(provider_name_key, DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"].get(provider_name_key, {})) 
                for key, value in config.items():
                    val_display = "*******" if "api_key" in key and value else value 
                    print(f"  - {key}: {val_display}")
        elif action == "use": 
            if len(args) < 2 or args[1].lower() not in ["gemini", "ollama"]:
                print("Usage: llm use <gemini|ollama>")
                return
            provider_name = args[1].lower()
            user_profile.add_preference("llm_provider_config", "active_provider", provider_name)
            print(f"Active LLM provider set to: {provider_name}. Restart Giblet for changes to take full effect in current session.")
        elif action == "config":
            if len(args) < 4:
                print("Usage: llm config <provider_name> <setting_key> <setting_value>")
                print("Valid providers: gemini, ollama")
                print("Valid keys for gemini: api_key, model_name")
                print("Valid keys for ollama: base_url, model_name")
                return
            provider_name = args[1].lower()
            key = args[2]
            value = " ".join(args[3:])
            user_profile.add_preference(("llm_provider_config", "providers", provider_name), key, value) 
            print(f"Set {key} = {value} for {provider_name}. Restart Giblet for changes to take full effect.")
        else:
            print(f"Unknown llm command: {action}. Use 'status', 'use', or 'config'.")
    register("llm", handle_llm_config, "Manages LLM provider configurations.")

    # Feedback Command
    def handle_feedback(args):
        if not args or args[0].lower() not in ['good', 'bad', 'ok', 'positive', 'negative', 'neutral']:
            print("Usage: feedback <good|bad|ok> [optional comment]")
            print("Example: feedback good Loved the creativity!")
            return

        rating_map = {"good": 5, "positive": 5,
                      "ok": 3, "neutral": 3,
                      "bad": 1, "negative": 1}
        rating_str = args[0].lower() 
        rating = rating_map.get(rating_str)
        if rating is None:
            print(f"Invalid feedback rating: '{rating_str}'. Please use 'good', 'ok', or 'bad'.")
            return

        comment = " ".join(args[1:]) if len(args) > 1 else ""

        last_interaction = memory.recall('last_ai_interaction')
        if isinstance(last_interaction, dict) and "context_id" in last_interaction and "output" in last_interaction:
            context_id = last_interaction["context_id"]
            user_profile.add_feedback(rating, comment, context_id=context_id)
        else:
            print("Warning: No valid last AI interaction found with context_id. Recording feedback without context.")
            user_profile.add_feedback(rating, comment)
        memory.remember('last_ai_interaction', None) 

    register("feedback", handle_feedback, "Provide feedback on the last AI-generated output.")

    # Skill Commands
    def handle_skills(args):
        if not args:
            print("Usage: skills <list|refresh|create_from_plan>")
            return
        
        action = args[0].lower()

        if action == "list":
            for skill_info in skill_manager.list_skills():
                print(f"  - {skill_info['name']}: {skill_info['description']}")
        elif action == "refresh":
            skill_manager.refresh_skills()
        elif action == "create_from_plan":
            if len(args) < 2:
                print("Usage: skills create_from_plan <NewSkillName> [Optional: \"trigger phrase for can_handle\"]")
                return
            
            new_skill_name = args[1]
            trigger_phrase = " ".join(args[2:]) if len(args) > 2 else None 
            if trigger_phrase:
                trigger_phrase = trigger_phrase.strip('"').strip("'")

            last_plan = memory.recall('last_plan')
            if not isinstance(last_plan, list) or not last_plan:
                print("❌ No valid 'last_plan' found in memory to create a skill from. Please run a plan first.")
                return

            print(f"\nGenerating skill '{new_skill_name}' from the following plan:")
            for i, step in enumerate(last_plan, 1):
                print(f"  Step {i}: giblet {step}")
            
            generated_skill_code = agent.generate_skill_from_plan(last_plan, new_skill_name, trigger_phrase)
            
            print("\n--- Generated Skill Code ---")
            print(generated_skill_code)
            print("--------------------------\n")

            confirm_save = input(f"Save this skill as '{new_skill_name.lower()}_skill.py' in the skills/ directory? (y/n): ").lower()
            if confirm_save == 'y':
                skill_filename = f"{new_skill_name.lower()}_skill.py"
                skill_filepath = SkillManager.SKILLS_DIR / skill_filename 
                if utils.write_file(str(skill_filepath.relative_to(utils.WORKSPACE_DIR)), generated_skill_code): 
                    print(f"✅ Skill '{new_skill_name}' saved to {skill_filepath}")
                    skill_manager.refresh_skills() 
                else:
                    print(f"❌ Failed to save skill '{new_skill_name}'.")
            else:
                print("Skill creation cancelled.")
        else:
            print(f"Unknown skills action: '{action}'. Valid actions: list, refresh, create_from_plan.")
    register("skills", handle_skills, "Manages and lists available agent skills.")

    # Proactive Learning Command
    def handle_learn_suggestions(args):
        if not proactive_learner_instance:
            print("❌ ProactiveLearner module could not be loaded. Suggestions unavailable.")
            return
        
        print("🧠 Attempting to generate proactive suggestions...")
        try:
            suggestions = proactive_learner_instance.generate_suggestions()

            if suggestions:
                print("\n--- Proactive Suggestions ---")
                for i, suggestion in enumerate(suggestions):
                    if "No specific proactive suggestions" in suggestion and len(suggestions) == 1:
                        print(f"   {suggestion}") 
                    else:
                        print(f" {i+1}. {suggestion}")
                print("---------------------------\n")
        except Exception as e:
            print(f"❌ Error generating suggestions: {e}")
            print("   Please ensure 'data/user_profile.json' is accessible and valid.")
    register("learn suggestions", handle_learn_suggestions, "Analyzes feedback & profile for proactive suggestions.")


    # History Command
    def handle_history(args):
        if not args or args[0].lower() not in ["commands", "analyze_patterns"]:
            print("Usage: history <commands|analyze_patterns> [options]")
            return
        
        action = args[0].lower()

        if action == "commands":
            limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
            command_log = memory.retrieve(command_manager.COMMAND_LOG_KEY)

            if isinstance(command_log, list) and command_log:
                print(f"\n--- Recent Command History (Last {limit}) ---")
                for entry in command_log[-limit:]:
                    print(f"  [{entry.get('timestamp')}] giblet {entry.get('command')} {' '.join(entry.get('args', []))}")
                print("--------------------------------------\n")
            else:
                print("No command history found.")
        elif action == "analyze_patterns":
            patterns = pattern_analyzer.analyze_command_history()
            if patterns:
                print("\n--- Potential Skill Candidates (Frequent Command Sequences) ---")
                for seq, count in patterns:
                    print(f"  - Sequence: {', '.join(seq)} (Occurred {count} times)")
                print("-------------------------------------------------------------\n")
                
                if patterns:
                    top_pattern_sequence, top_pattern_count = patterns[0]
                    print(f"[Proactive Suggestion] Would you like to try creating a skill from the most frequent pattern: `{' -> '.join(top_pattern_sequence)}` (used {top_pattern_count} times)?")
                    create_skill_q = input("Enter 'y' to create skill, or press Enter to skip: ").lower()
                    
                    if create_skill_q == 'y':
                        chosen_sequence_list = list(top_pattern_sequence)
                        skill_name_suggestion = f"Auto{chosen_sequence_list[0].capitalize()}{chosen_sequence_list[1].capitalize() if len(chosen_sequence_list) > 1 else ''}Skill"
                        new_skill_name = input(f"Enter a name for the new skill (default: {skill_name_suggestion}): ") or skill_name_suggestion
                        trigger_phrase = input(f"Enter an optional trigger phrase for '{new_skill_name}' (e.g., \"perform my common task\"): ") or None
                        if trigger_phrase:
                            trigger_phrase = trigger_phrase.strip('"').strip("'")

                        generated_skill_code = agent.generate_skill_from_plan(chosen_sequence_list, new_skill_name, trigger_phrase)
                        
                        print("\n--- Generated Skill Code ---")
                        print(generated_skill_code)
                        print("--------------------------\n")

                        confirm_save = input(f"Save this skill as '{new_skill_name.lower()}_skill.py' in the skills/ directory? (y/n): ").lower()
                        if confirm_save == 'y':
                            safe_skill_name_for_file = "".join(c if c.isalnum() else "_" for c in new_skill_name).lower()
                            skill_filename = f"{safe_skill_name_for_file}_skill.py"
                            relative_skill_path = SKILLS_DIR.relative_to(utils.WORKSPACE_DIR) / skill_filename
                            if utils.write_file(str(relative_skill_path), generated_skill_code): 
                                print(f"✅ Skill '{new_skill_name}' saved to {SKILLS_DIR / skill_filename}")
                                skill_manager.refresh_skills() 
                            else:
                                print(f"❌ Failed to save skill '{new_skill_name}'.")

    register("history", handle_history, "Views command history.")
    
    # --- Genesis Mode Commands ---
    def handle_genesis(args):
        valid_subcommands = ["start", "generate-readme", "generate-roadmap", "scaffold", "publish", "random", "log"]
        if not args or args[0].lower() not in valid_subcommands:
            print("Usage: genesis <subcommand> [options...]")
            print(f"Valid subcommands: {', '.join(valid_subcommands)}")
            print("  start \"<idea>\"           - Begin the interactive idea interpretation.")
            print("  random                     - Generate a random, weird idea and start interpretation.")
            print("  generate-readme          - Generate a README.md from the last brief.")
            print("  generate-roadmap         - Generate a roadmap.md from the last brief.")
            print("  scaffold                   - Scaffold a local project from the last brief.")
            print("  publish                    - Create a GitHub repo from the last brief.")
            print("  log <name> \"<brief>\"   - (Dev) Log a manual project creation.")
            return
        
        subcommand = args[0].lower()

        if subcommand == "start":
            if len(args) < 2:
                print("Usage: genesis start \"<your initial project idea>\"")
                return
            initial_idea = " ".join(args[1:])
            _run_genesis_interview(initial_idea, idea_interpreter_cli, memory)
        
        elif subcommand == "random":
            print("🎲 Summoning a strange and wonderful new project idea...")
            try:
                response = httpx.post("http://localhost:8000/ideas/random_weird", timeout=60)
                response.raise_for_status()
                data = response.json()
                random_idea = data.get("idea")
                
                if random_idea:
                    _run_genesis_interview(random_idea, idea_interpreter_cli, memory)
                else:
                    print("❌ The API did not return a random idea.")
            except Exception as e:
                print(f"❌ Failed to get a random idea from the API: {e}")

        elif subcommand == "generate-readme":
            print("\nGenerating Project README...")
            last_brief = memory.recall("last_genesis_brief")
            if not isinstance(last_brief, dict) or not last_brief:
                print("❌ No project brief found in memory. Please run `genesis start` first.")
                return
            
            current_readme_style_settings = style_manager_for_cli.get_style().get('readme', {})
            readme_content = readme_generator_cli.generate(last_brief)
            print("\n--- Generated README.md ---\n")
            print(readme_content)
            print("\n---------------------------\n")

            if current_readme_style_settings:
                save_style_confirm = input("Save this README style as your default? (y/n): ").lower()
                if save_style_confirm == 'y':
                    try:
                        payload = {"category": "readme", "settings": current_readme_style_settings}
                        response = httpx.post("http://localhost:8000/style/set_preferences", json=payload, timeout=10)
                        response.raise_for_status()
                        print("✅ README style preferences saved as default!")
                    except Exception as e:
                        print(f"❌ Failed to save style preferences: {e}")
            else:
                print("ℹ️ No specific README style settings were actively used for this generation to save as default.")
            
            save_file_confirm = input("Save this content to README.md? (y/n): ").lower()
            if save_file_confirm == 'y':
                if utils.write_file("README.md", readme_content):
                    print("✅ README.md saved successfully!")
                else:
                    print("❌ Failed to save README.md.")
            else:
                print("Save to file cancelled.")

        elif subcommand == "generate-roadmap":
            print("\nGenerating Project Roadmap...")
            last_brief = memory.recall("last_genesis_brief")

            if not isinstance(last_brief, dict) or not last_brief:
                print("❌ No project brief found in memory. Please run `genesis start` first.")
                return
            
            roadmap_content = roadmap_generator_cli.generate(last_brief)
            print("\n--- Generated roadmap.md ---\n")
            print(roadmap_content)
            print("\n----------------------------\n")
            
            save_confirm = input("Save this content to roadmap.md? (y/n): ").lower()
            if save_confirm == 'y':
                if utils.write_file("roadmap.md", roadmap_content):
                    print("✅ roadmap.md saved successfully!")
                else:
                    print("❌ Failed to save roadmap.md.")
            else:
                print("Save cancelled.")

        elif subcommand == "scaffold":
            print("\n🏗️ Scaffolding local project...")
            last_brief = memory.recall("last_genesis_brief")
            if not isinstance(last_brief, dict) or not last_brief:
                print("❌ No project brief found in memory. Please run `genesis start` first.")
                return

            project_name = last_brief.get("title", "new_giblet_project")
            payload = {
                "project_name": project_name,
                "project_brief": last_brief
            }

            try:
                response = httpx.post("http://localhost:8000/project/scaffold_local", json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                print(f"✅ {data.get('message', 'Local project scaffolded successfully.')}")
                if data.get('path'):
                     print(f"   Project path: {data.get('path')}")
            except httpx.RequestError as e:
                print(f"❌ API Request Failed: Could not connect to the Giblet API at http://localhost:8000. Is the server running?")
            except httpx.HTTPStatusError as e:
                 print(f"❌ API returned error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"❌ An unexpected error occurred during scaffolding: {e}")

        elif subcommand == "publish":
            print("\n☁️ Creating GitHub repository...")
            last_brief = memory.recall("last_genesis_brief")
            if not isinstance(last_brief, dict) or not last_brief:
                print("❌ No project brief found in memory. Please run `genesis start` first.")
                return

            repo_name = last_brief.get("title", "new-giblet-project").lower().replace(" ", "-")
            description = last_brief.get("summary", "A new project generated by The Giblet.")
            payload = {"repo_name": repo_name, "description": description, "private": True}

            try:
                response = httpx.post("http://localhost:8000/project/create_github_repo", json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                print(f"✅ {data.get('message', 'GitHub repository created successfully.')}")
            except Exception as e:
                print(f"❌ Failed to create GitHub repository: {e}")

        elif subcommand == "log":
            if len(args) < 3:
                print("Usage: genesis log <project_name> \"<initial_brief>\"")
                return

            project_name_arg = args[1]
            initial_brief_arg = " ".join(args[2:])
            
            placeholder_settings = {
                "readme_style": style_manager_for_cli.get_preference("readme.default_style", "standard"),
                "roadmap_format": style_manager_for_cli.get_preference("roadmap.default_format", "phase_based"),
                "tone": style_manager_for_cli.get_preference("general_tone", "neutral")
            }

            genesis_logger_cli.log_project_creation(
                project_name=project_name_arg,
                initial_brief=initial_brief_arg,
                genesis_settings_used=placeholder_settings,
            )
    register("genesis", handle_genesis, "Manages project genesis and document generation.")

    # --- Just-in-Time Proactive Suggestions Function ---
    def display_just_in_time_suggestions(last_command_name: str | None, last_args: list | None = None):
        if not proactive_learner_instance or not project_contextualizer_cli:
            return 
        if last_args is None:
            last_args = []

        jit_suggestions = []

        if last_command_name == "git status":
            pass 

        elif last_command_name == "generate function":
            last_file_written = memory.recall('last_file_written') 
            jit_suggestions.append("💡 Quick Tip: Generated a function? Consider writing tests with `generate tests <filepath>` or refactoring with `refactor <filepath> \"instruction\"`.")

        elif last_command_name == "plan":
            if memory.recall('last_plan'): 
                jit_suggestions.append("💡 Quick Tip: Plan created! Use `execute` to run it.")

        elif last_command_name == "read" and last_args and last_args[0].endswith(".py"):
            filepath_read = last_args[0]
            jit_suggestions.append(f"💡 Quick Tip: Just viewed `{filepath_read}`. Need to refactor it? Try `refactor {filepath_read} \"your instruction\"`.")

        elif last_command_name == "write":
            last_file_written = memory.recall('last_file_written')
            if last_file_written and last_file_written.endswith(".py"):
                 jit_suggestions.append(f"💡 Quick Tip: Just wrote to `{last_file_written}`. Maybe generate tests for it with `generate tests {last_file_written}`?")

        elif last_command_name == "focus" and last_args and last_args[0] != '--clear':
            current_focus_text = " ".join(last_args)
            jit_suggestions.append(f"💡 Quick Tip: Focus set to '{current_focus_text}'. You can now use `plan \"achieve my focus\"` or generate ideas with `idea about my current focus`.")

        if not jit_suggestions:
            learner_suggestions = proactive_learner_instance.generate_suggestions()
            if learner_suggestions and not ("No specific proactive suggestions" in learner_suggestions[0] and len(learner_suggestions) ==1) :
                jit_suggestions.append(f"💡 Quick Tip: {learner_suggestions[0]}") 

        if jit_suggestions:
            print("\n" + "\n".join(list(set(jit_suggestions)))) 

    for plugin in plugin_manager.plugins:
        plugin.register_commands(command_manager)

    print("\n[DEBUG] Registered commands before main loop:")
    if command_manager.commands:
        for cmd_name in sorted(command_manager.commands.keys()):
            print(f"  - {cmd_name}")
    else:
        print("  - No commands registered in CommandManager.")
    print("[DEBUG] End of registered commands list.\n")

    print("🧠 The Giblet is awake. All commands registered. Type 'help' for a list of commands.")
    
    command_execution_count = 0
    PROACTIVE_ANALYSIS_THRESHOLD = 5 
    JIT_SUGGESTION_THRESHOLD = 2 

    while True:
        try:
            current_focus = memory.recall("current_focus")
            prompt_text = f" giblet [focus: {current_focus[:20]}...]>" if current_focus and isinstance(current_focus, str) and not current_focus.startswith("I don't have a memory for") else f" giblet [branch: {git_analyzer.repo.active_branch.name}]>" if git_analyzer.repo else " giblet> "
            
            user_input = input(prompt_text).strip()
            if not user_input: continue

            parts = user_input.split(" ", 1)
            command_name = parts[0].lower()
            
            potential_multi_word_command = command_name
            temp_args_str = parts[1] if len(parts) > 1 else ""
            
            if temp_args_str:
                first_arg = temp_args_str.split(" ", 1)[0]
                if f"{command_name} {first_arg}" in command_manager.commands:
                    command_name = f"{command_name} {first_arg}"
                    args_str = temp_args_str.split(" ", 1)[1] if " " in temp_args_str else ""
                    args = shlex.split(args_str) 
                else:
                    args = shlex.split(temp_args_str) 
            else:
                args = []
            
            executed_command_name = command_name 
            executed_args = args 
            command_manager.execute(executed_command_name, executed_args)
            command_execution_count += 1

            if command_execution_count % PROACTIVE_ANALYSIS_THRESHOLD == 0:
                patterns = pattern_analyzer.analyze_command_history(min_len=2, max_len=3, min_occurrences=3) 
                if patterns:
                    if patterns:
                        top_pattern_sequence, top_pattern_count = patterns[0]
                        print(f"[Proactive Suggestion] Would you like to try creating a skill from the most frequent pattern: `{' -> '.join(top_pattern_sequence)}` (used {top_pattern_count} times)?")
                        create_skill_q = input("Enter 'y' to create skill, or press Enter to skip: ").lower()
                        if create_skill_q == 'y':
                            chosen_sequence_list = list(top_pattern_sequence)
                            skill_name_suggestion = f"Auto{chosen_sequence_list[0].capitalize()}{chosen_sequence_list[1].capitalize() if len(chosen_sequence_list) > 1 else ''}Skill"
                            new_skill_name = input(f"Enter a name for the new skill (default: {skill_name_suggestion}): ") or skill_name_suggestion
                            trigger_phrase = input(f"Enter an optional trigger phrase for '{new_skill_name}' (e.g., \"perform my common task\"): ") or None
                            if trigger_phrase:
                                trigger_phrase = trigger_phrase.strip('\"').strip("'")
                            generated_skill_code = agent.generate_skill_from_plan(chosen_sequence_list, new_skill_name, trigger_phrase)
                            print("\n--- Generated Skill Code ---")
                            print(generated_skill_code)
                            print("--------------------------\n")
                            confirm_save = input(f"Save this skill as '{new_skill_name.lower()}_skill.py' in the skills/ directory? (y/n): ").lower()
                            if confirm_save == 'y':
                                safe_skill_name_for_file = "".join(c if c.isalnum() else "_" for c in new_skill_name).lower()
                                skill_filename = f"{safe_skill_name_for_file}_skill.py"
                                relative_skill_path = SKILLS_DIR.relative_to(utils.WORKSPACE_DIR) / skill_filename
                                if utils.write_file(str(relative_skill_path), generated_skill_code):
                                    print(f"✅ Skill '{new_skill_name}' saved to {SKILLS_DIR / skill_filename}")
                                    skill_manager.refresh_skills()
                                else:
                                    print(f"❌ Failed to save skill '{new_skill_name}'.")
            
            if command_execution_count % JIT_SUGGESTION_THRESHOLD == 0:
                display_just_in_time_suggestions(executed_command_name, executed_args)

        except KeyboardInterrupt:
            print("\n🧠 Going to sleep. Goodbye!")
            break 
