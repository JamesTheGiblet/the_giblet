# ui/cli.py
import argparse
import os
import json
import logging
import subprocess
import sys
import webbrowser
import time
from pathlib import Path
import shlex
import httpx

# --- Core Module Imports ---
from core import roadmap_manager, utils
from core.memory import Memory
from core.idea_synth import IdeaSynthesizer
from core.automator import Automator
from core.git_analyzer import GitAnalyzer
from core.code_generator import CodeGenerator
from core.command_manager import CommandManager
from core.plugin_manager import PluginManager
from core.watcher import start_watching
from core.agent import Agent
from core.user_profile import DEFAULT_PROFILE_STRUCTURE, UserProfile
from core.skill_manager import SKILLS_DIR, SkillManager
from core.pattern_analyzer import PatternAnalyzer
from core.llm_provider_base import LLMProvider
from core.capability_assessor import CapabilityAssessor
from core.llm_providers import GeminiProvider, OllamaProvider
from core.style_preference import StylePreferenceManager
from core.genesis_logger import GenesisLogger
from core.project_contextualizer import ProjectContextualizer
from core.idea_interpreter import IdeaInterpreter
from core.modularity_guardrails import ModularityGuardrails # Added import
from core.mini_readme_generator import MiniReadmeGenerator
from core.readme_generator import ReadmeGenerator
from core.roadmap_generator import RoadmapGenerator
from core.duplication_analyzer import DuplicationAnalyzer # <<< 1. IMPORT aNALYZER
from ui.cli_components import display_duplication_report
from ui.cli_genesis_flow import run_genesis_interview
from ui.cli_execution_flow import execute_plan_with_self_correction # NEW IMPORT
from ui.cli_config_commands import handle_profile_command, handle_llm_config_command # NEW IMPORT
from ui.cli_genesis_commands import handle_genesis as handle_genesis_command # NEW IMPORT

# --- Proactive Learner Import (now uses actual UserProfile) ---
try:
    from core.proactive_learner import ProactiveLearner
    from core.modularity_guardrails import ModularityGuardrails # Re-import for clarity, though already imported
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

    # Instantiate RoadmapManager for local 'todo' commands
    roadmap_manager_cli = roadmap_manager.RoadmapManager(memory_system=memory, style_preference_manager=style_manager_for_cli)

    automator = Automator()
    git_analyzer = GitAnalyzer()
    command_manager = CommandManager()
    project_contextualizer_cli = ProjectContextualizer(memory_system=memory, project_root=".")

    # --- Instantiate All Core Components ---
    idea_synth = IdeaSynthesizer(user_profile=user_profile, memory_system=memory, llm_provider=cli_llm_provider,
                                 project_contextualizer=project_contextualizer_cli,
                                 style_preference_manager=style_manager_for_cli)
    code_generator = CodeGenerator(user_profile=user_profile, memory_system=memory, llm_provider=cli_llm_provider, project_contextualizer=project_contextualizer_cli)
    mini_readme_generator_cli = MiniReadmeGenerator(
        llm_provider=cli_llm_provider,
        style_manager=style_manager_for_cli,
        user_profile=user_profile
    )
    readme_generator_cli = ReadmeGenerator(
        llm_provider=cli_llm_provider,
        style_manager=style_manager_for_cli
    )
    roadmap_generator_cli = RoadmapGenerator(
        llm_provider=cli_llm_provider,
        style_manager=style_manager_for_cli
    )
    idea_interpreter_cli = IdeaInterpreter(
        llm_provider=cli_llm_provider,
        user_profile=user_profile,
        memory=memory,
        style_manager=style_manager_for_cli,
        project_contextualizer=project_contextualizer_cli,
        readme_generator=readme_generator_cli,
        roadmap_generator=roadmap_generator_cli
    )
    proactive_learner_instance = ProactiveLearner(user_profile=user_profile) if ProactiveLearner is not None else None
    skill_manager = SkillManager(user_profile=user_profile, memory=memory, command_manager_instance=command_manager)
    agent = Agent(idea_synth=idea_synth, code_generator=code_generator, skill_manager=skill_manager)
    pattern_analyzer = PatternAnalyzer(memory_system=memory)
    plugin_manager = PluginManager()
    
    # <<< 2. INSTANTIATE DuplicationAnalyzer
    duplication_analyzer = DuplicationAnalyzer(
        project_root='.', 
        llm_provider=cli_llm_provider, 
        user_profile=user_profile
    )
    
    # --- Register All Commands ---
    def register(name, handler, description=""):
        command_manager.register(name, handler, description)

    # --- Command Handlers ---

    def handle_help(args):
        print("\n--- The Giblet CLI: Help ---")
        for name, data in sorted(command_manager.commands.items()):
            print(f"  {name:<30} - {data['description']}")
        print("----------------------------\n")
        print("Analysis Commands:")
        print("  analyze duplicates         - Scans for structural and conceptual code duplication.")
        print("\nAgent Commands:")
        print("  plan \"<goal>\"              - Creates a multi-step plan to achieve a goal.")
        print("  execute                    - Executes the most recently created plan.")
        print("\nUser Profile Commands:")
        print("  profile get [<cat> [<key>]] - Gets a profile value or the whole profile.")
        print("  profile set <cat> <key> <val> - Sets a profile value.")
        print("  profile clear              - Clears the entire user profile.")
        print("\nLLM Configuration Commands:")
        print("  genesis start \"<idea>\"     - Begins the Genesis Mode idea interpretation.")
        print("  gauntlet edit              - Opens the Gauntlet Test Editor UI.")
        print("  assess model               - Runs capability tests on the current LLM.")
        print("  llm status                 - Shows current LLM provider and model.")
        print("  llm use <gemini|ollama>    - Sets the active LLM provider.")
        print("  llm config <provider> <key> <value> - Configure provider-specific settings.")
        print("  feedback <rating> [comment] - Provide feedback on the last AI output.")
        print("\nSkill Commands:")
        print("  skills list                - Lists available skills.")
        print("  skills refresh             - Re-scans the skills directory.")
        print("  skills create_from_plan <SkillName> [\"trigger phrase\"] - Generates a new skill from the last executed plan.")
        print("\nHistory Commands:")
        print("  learn suggestions          - Analyzes feedback & profile for proactive suggestions.")
        print("  history analyze_patterns   - Analyzes command history for potential skill candidates.")
        print("  history commands [limit]   - Shows recent command history.")
    register("help", handle_help, "Shows this help message.")

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
            except EOFError:
                break
        content = "\n".join(lines)
        if utils.write_file(filepath, content):
            memory.remember('last_file_written', filepath)
            print(f"✅ Content written to {filepath}")
        else:
            print(f"❌ Failed to write to {filepath}")

    register("read", lambda args: utils.read_file(args[0]) if args else print("Usage: read <filepath>"), "Reads a file.")
    register("write", handle_write, "Writes content to a file.")
    register("ls", lambda args: print('\n'.join(utils.list_files(args[0] if args else "."))), "Lists files.")
    register("exec", lambda args: utils.execute_command(" ".join(args)), "Executes a shell command.")
    
    register("remember", lambda args: memory.remember(args[0], " ".join(args[1:])) if len(args) > 1 else print("Usage: remember <key> <value>"), "Saves to session memory.")
    register("recall", lambda args: print(memory.recall(args[0])) if args else print("Usage: recall <key>"), "Recalls from session memory.")
    register("commit", lambda args: memory.commit(args[0], " ".join(args[1:])) if len(args) > 1 else print("Usage: commit <key> <value>"), "Saves to long-term memory.")
    register("retrieve", lambda args: print(memory.retrieve(args[0])) if args else print("Usage: retrieve <key>"), "Retrieves from long-term memory.")

    register("checkpoint", lambda args: memory.save_checkpoint(args[1]) if len(args) > 1 and args[0] == 'save' else (memory.load_checkpoint(args[1]) if len(args) > 1 and args[0] == 'load' else print("Usage: checkpoint [save|load] <name>")), "Saves or loads a session checkpoint.")
    register("focus", lambda args: memory.remember("current_focus", None) or print("Focus cleared.") if args and args[0] == '--clear' else (memory.remember("current_focus", " ".join(args)) or print(f"Focus set to: {' '.join(args)}")) if args else print(f"Current focus: {memory.recall('current_focus')}"), "Sets or clears the session focus.")

    def handle_roadmap(args):
        print("🗺️  Fetching roadmap from Giblet API...")
        try:
            response = httpx.get("http://localhost:8000/roadmap")
            response.raise_for_status()
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
        except httpx.RequestError:
            print("❌ API Request Failed: Could not connect to the Giblet API at http://localhost:8000. Is the server running?")
        except Exception as e:
            print(f"❌ An error occurred: {e}")
    register("roadmap", handle_roadmap, "Views the project roadmap via the API.")
    register("git", lambda args: (print(git_analyzer.get_branch_status()) if args[0] == 'status' else print('\n'.join(git_analyzer.list_branches())) if args[0] == 'branches' else print('\n'.join(str(c) for c in git_analyzer.get_commit_log())) if args[0] == 'log' else print(git_analyzer.summarize_recent_activity(idea_synth)) if args[0] == 'summary' else print("Usage: git [status|branches|log|summary]")), "Interacts with the Git repository.")

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
                Path("tests").mkdir(exist_ok=True)
                utils.write_file(test_filename, generated_tests)
                print(f"\n✅ Successfully generated tests. Saved to '{test_filename}'")
                print(f"   To run them, exit The Giblet and use the command: pytest")
        else:
            print(f"Unknown generate command: '{gen_type}'. Try 'function' or 'tests'.")
    register("generate", handle_generate, "Generates code or tests.")
    register("build", lambda args: utils.write_file(f"ui_for_{Path(args[1]).stem}.py", code_generator.generate_streamlit_ui(utils.read_file(args[1]), args[1])) if len(args) > 1 and args[0] == 'ui' else print("Usage: build ui <filepath>"), "Builds a UI from a data model.")
    register("refactor", lambda args: utils.write_file(args[0], code_generator.refactor_code(utils.read_file(args[0]), args[1])) if len(args) > 1 and 'y' == input("Overwrite? (y/n): ").lower() else print("Refactor cancelled."), "Refactors a file based on an instruction.")

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
                print('Usage: todo add "@<user>" "<description>"')
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

    # --- Agent & Plan Execution Handlers ---
    def handle_execute(args):
        plan = memory.recall('last_plan')
        if not isinstance(plan, list) or not plan:
            print("❌ No plan found in memory. Please generate a plan first using the 'plan' command.")
            if isinstance(plan, str):
                print(f"   (Details: {plan})")
            return
        execute_plan_with_self_correction(plan, memory, command_manager, agent)
    register("execute", handle_execute, "Executes the most recently created plan.")

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
    register("plan", handle_plan, "Creates a multi-step plan to achieve a goal.")

    def handle_watch(args):
        start_watching()
    register("watch", handle_watch, "Enters watch mode to provide proactive suggestions on file changes.")

    # --- Profile & LLM Configuration Handlers ---
    def profile_command_wrapper(args):
        handle_profile_command(args, user_profile)
    register("profile", profile_command_wrapper, "Manages user profile settings.")

    def handle_gauntlet_edit(args):
        print("🚀 Launching Gauntlet Test Editor...")
        try:
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", "gauntlet_editor.py"])
            print("   Editor should open in your web browser. If not, ensure Streamlit is installed.")
        except Exception as e:
            print(f"❌ Failed to launch Gauntlet Editor: {e}")
    register("gauntlet edit", handle_gauntlet_edit, "Opens the interactive Gauntlet Test Editor.")

    def llm_config_command_wrapper(args):
        handle_llm_config_command(args, user_profile)
    register("llm", llm_config_command_wrapper, "Manages LLM provider configurations.")

    def handle_feedback(args):
        if not args or args[0].lower() not in ['good', 'bad', 'ok', 'positive', 'negative', 'neutral']:
            print("Usage: feedback <good|bad|ok> [optional comment]")
            return

        rating_map = {"good": 5, "positive": 5, "ok": 3, "neutral": 3, "bad": 1, "negative": 1}
        rating_str = args[0].lower() 
        rating = rating_map.get(rating_str)
        if rating is None:
            print(f"Invalid feedback rating: '{rating_str}'.")
            return

        comment = " ".join(args[1:]) if len(args) > 1 else ""
        last_interaction = memory.recall('last_ai_interaction')
        if isinstance(last_interaction, dict) and "context_id" in last_interaction:
            user_profile.add_feedback(rating, comment, context_id=last_interaction["context_id"])
        else:
            print("Warning: No valid last AI interaction found. Recording feedback without context.")
            user_profile.add_feedback(rating, comment)
        memory.remember('last_ai_interaction', None) 
    register("feedback", handle_feedback, "Provide feedback on the last AI-generated output.")

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
                print("Usage: skills create_from_plan <NewSkillName> [Optional: \"trigger phrase\"]")
                return
            
            new_skill_name = args[1]
            trigger_phrase = " ".join(args[2:]).strip('"\'') if len(args) > 2 else None
            last_plan = memory.recall('last_plan')
            if not isinstance(last_plan, list) or not last_plan:
                print("❌ No valid 'last_plan' found in memory to create a skill from.")
                return

            print(f"\nGenerating skill '{new_skill_name}' from the following plan:")
            for i, step in enumerate(last_plan, 1):
                print(f"  Step {i}: giblet {step}")
            
            generated_skill_code = agent.generate_skill_from_plan(last_plan, new_skill_name, trigger_phrase)
            
            print("\n--- Generated Skill Code ---\n" + generated_skill_code + "\n--------------------------\n")
            confirm_save = input(f"Save this skill as '{new_skill_name.lower()}_skill.py'? (y/n): ").lower()
            if confirm_save == 'y':
                skill_filename = f"{new_skill_name.lower()}_skill.py"
                skill_filepath = SKILLS_DIR / skill_filename 
                if utils.write_file(str(skill_filepath.relative_to(utils.WORKSPACE_DIR)), generated_skill_code): 
                    print(f"✅ Skill '{new_skill_name}' saved to {skill_filepath}")
                    skill_manager.refresh_skills() 
                else:
                    print(f"❌ Failed to save skill '{new_skill_name}'.")
            else:
                print("Skill creation cancelled.")
        else:
            print(f"Unknown skills action: '{action}'.")
    register("skills", handle_skills, "Manages and lists available agent skills.")

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
    register("learn suggestions", handle_learn_suggestions, "Analyzes feedback & profile for proactive suggestions.")

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
                    print(f"[Proactive Suggestion] Create a skill from the most frequent pattern: `{' -> '.join(top_pattern_sequence)}` ({top_pattern_count} times)?")
                    create_skill_q = input("Enter 'y' to create skill, or press Enter to skip: ").lower()
                    
                    if create_skill_q == 'y':
                        chosen_sequence_list = list(top_pattern_sequence)
                        skill_name_suggestion = f"Auto{chosen_sequence_list[0].capitalize()}{chosen_sequence_list[1].capitalize() if len(chosen_sequence_list) > 1 else ''}Skill"
                        new_skill_name = input(f"Enter a name for the new skill (default: {skill_name_suggestion}): ") or skill_name_suggestion
                        trigger_phrase = input(f"Enter an optional trigger phrase for '{new_skill_name}': ") or None
                        if trigger_phrase:
                            trigger_phrase = trigger_phrase.strip('"\'')

                        generated_skill_code = agent.generate_skill_from_plan(chosen_sequence_list, new_skill_name, trigger_phrase)
                        
                        print("\n--- Generated Skill Code ---\n" + generated_skill_code + "\n--------------------------\n")
                        confirm_save = input(f"Save this skill as '{new_skill_name.lower()}_skill.py'? (y/n): ").lower()
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

    # <<< 3. ADD NEW HANDLER FOR 'analyze duplicates'
    def handle_analyze_duplicates(args):
        """Runs the duplication analyzer and prints a formatted report."""
        report = duplication_analyzer.analyze()        
        display_duplication_report(report)

    # <<< 4. REGISTER THE NEW COMMAND
    register("analyze duplicates", handle_analyze_duplicates, "Scans for duplicate code.")

    # --- Modularity Guardrails Command ---
    def handle_modularity(args):
        if args.check:
            project_root = os.getcwd() # Or get from a config/argument for multi-project support
            guardrails = ModularityGuardrails()
            long_files = guardrails.scan_project(project_root, args.ext, args.threshold)
            suggestions = guardrails.suggest_refactoring(long_files)
            print(suggestions)
        else:
            print("Usage: giblet modularity --check [--threshold <lines>] [--ext <.ext1> <.ext2>...]")
    register("modularity", handle_modularity, "Checks for code modularity issues (e.g., long files).")

    # --- Genesis Command ---
    def genesis_command_wrapper(args):
        """Wrapper to pass dependencies to the external genesis handler."""
        handle_genesis_command(
            args,
            idea_interpreter_cli,
            memory,
            readme_generator_cli,
            roadmap_generator_cli,
            genesis_logger_cli,
            style_manager_for_cli
        )
    register("genesis", genesis_command_wrapper, "Manages project genesis and document generation.")

    def display_just_in_time_suggestions(last_command_name: str | None, last_args: list | None = None):
        if not proactive_learner_instance or not project_contextualizer_cli:
            return 
        if last_args is None:
            last_args = []

        jit_suggestions = []
        if last_command_name == "generate function":
            jit_suggestions.append("💡 Tip: Generated a function? Consider writing tests with `generate tests <filepath>`.")
        elif last_command_name == "plan":
            if memory.recall('last_plan'): 
                jit_suggestions.append("💡 Tip: Plan created! Use `execute` to run it.")

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

    print("🧠 The Giblet is awake. Type 'help' for a list of commands.")
    
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
                    top_pattern_sequence, _ = patterns[0]
                    print(f"[Proactive Suggestion] Create skill from frequent pattern: `{' -> '.join(top_pattern_sequence)}`?")
                    if input("Enter 'y' to create: ").lower() == 'y':
                        # Simplified skill creation flow for brevity
                        skill_name = input("Enter a name for the new skill: ")
                        if skill_name:
                            handle_skills(["create_from_plan", skill_name])

            if command_execution_count % JIT_SUGGESTION_THRESHOLD == 0:
                display_just_in_time_suggestions(executed_command_name, executed_args)

        except KeyboardInterrupt:
            print("\n🧠 Going to sleep. Goodbye!")
            break