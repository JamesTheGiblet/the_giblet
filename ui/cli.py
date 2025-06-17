# ui/cli.py
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
from core.user_profile import UserProfile # New import for UserProfile
from core.skill_manager import SkillManager # New import for SkillManager
from core.pattern_analyzer import PatternAnalyzer # New import

def start_cli_loop():
    """Starts the main interactive loop for The Giblet."""
    # --- Initialization ---
    memory = Memory() # Memory first
    user_profile = UserProfile(memory_system=memory) # UserProfile needs memory
    idea_synth = IdeaSynthesizer(user_profile=user_profile, memory_system=memory) # Pass profile and memory
    code_generator = CodeGenerator(user_profile=user_profile, memory_system=memory) # Pass profile and memory
    automator = Automator()
    git_analyzer = GitAnalyzer()
    command_manager = CommandManager()
    skill_manager = SkillManager(user_profile=user_profile, memory=memory, command_manager_instance=command_manager) # Instantiate SkillManager
    agent = Agent(idea_synth=idea_synth, code_generator=code_generator, skill_manager=skill_manager) # Pass skill_manager
    pattern_analyzer = PatternAnalyzer(memory_system=memory) # Instantiate PatternAnalyzer
    plugin_manager = PluginManager()
    MAX_FIX_ATTEMPTS = 3 # Define how many times to attempt self-correction
    
    # --- Register All Commands ---
    def register(name, handler, description=""):
        command_manager.register(name, handler, description)

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
        print("  feedback <rating> [comment] - Provide feedback on the last AI output (rating: good, bad, ok).")
        print("\nSkill Commands:")
        print("  skills list                - Lists available skills.")
        print("  skills refresh             - Re-scans the skills directory.")
        print("  skills create_from_plan <SkillName> [\"trigger phrase\"] - Generates a new skill from the last executed plan.")
        print("\nHistory Commands:")
        print("  history analyze_patterns   - Analyzes command history for potential skill candidates.")
        print("  history commands [limit]   - Shows recent command history (default limit 10).")
    register("help", handle_help, "Shows this help message.")

    # File Commands
    # <<< UPDATED: 'write' command handler
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
    # <<< UPDATED: 'exec' handler to return results for self-correction
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
    # <<< UPDATED: The new handler for the 'roadmap' command
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
            # The full argument string for 'add' is everything after 'todo add '
            arg_string = " ".join(args[1:])
            try:
                # Use shlex to correctly parse arguments with quotes
                parsed_args = shlex.split(arg_string)
                if len(parsed_args) != 2:
                    raise ValueError("Invalid number of arguments for 'todo add'")

                assignee, description = parsed_args

                if not assignee.startswith('@'):
                    raise ValueError("Assignee must start with '@'")

                # This will now cause an error as roadmap_manager is not defined.
                # This part of the code would need to be refactored to use an API
                # or have roadmap_manager re-instantiated if 'todo' commands
                # are to remain functional with the local RoadmapManager.
                roadmap_manager.add_shared_task(description, assignee)

            except ValueError as e:
                print(f"Error: {e}")
                print('Usage: todo add "@<user>" "<description>" (ensure description is quoted if it contains spaces)')
        elif sub_command == "list":
            tasks = roadmap_manager.view_shared_tasks()
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
        # Check if a process is already stored in session memory and is still running
        existing_process = memory.recall('streamlit_process')
        if existing_process and isinstance(existing_process, subprocess.Popen) and existing_process.poll() is None:
            print("Dashboard is already running. Opening a new browser tab to http://localhost:8501...")
            webbrowser.open("http://localhost:8501")
            return

        #  If no process is running, launch a new one
        print("🚀 Launching The Giblet Dashboard...")
        print("   If a browser tab doesn't open, please navigate to http://localhost:8501")
        try:
            # Start the streamlit server as a background process
            new_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.runOnSave", "true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Store the new process object in session memory
            memory.remember('streamlit_process', new_process)
            # Give the server a moment to start up
            time.sleep(3)
            # Explicitly open the web browser
            webbrowser.open("http://localhost:8501")
        except Exception as e:
            print(f"❌ Failed to launch dashboard: {e}")
    register("dashboard", handle_dashboard, "Launches or focuses the web dashboard.")

    # 3. Add the new command handler function in start_cli_loop()
    def handle_watch(args):
        start_watching()
    register("watch", handle_watch, "Enters watch mode to provide proactive suggestions on file changes.")

    # 4. Add the new command handler function and registration
    # 2. Update the `handle_plan` function to save the plan
    def handle_plan(args):
        if not args:
            print("Usage: plan \"<your high-level goal>\"")
            return

        goal = " ".join(args)
        plan = agent.create_plan(goal)

        print("\n--- Generated Plan ---")
        if plan and not (isinstance(plan, list) and len(plan) > 0 and "Failed to generate" in plan[0]):
            # <<< NEW: Save the plan to session memory
            memory.remember('last_plan', plan)
            for i, step in enumerate(plan, 1):
                print(f"Step {i}: giblet {step}")
            print("----------------------\n")
            print("To run this plan, use the 'execute' command.")
        elif isinstance(plan, list) and len(plan) > 0 :
            print(plan[0]) # Print the failure message
            print("----------------------\n")
        else:
            print("Failed to generate a plan or the plan was empty.")
            print("----------------------\n")

    # <<< UPDATED: handle_execute with self-correction logic
    def handle_execute(args):
        plan = memory.recall('last_plan')
        # Check if the plan is a list and not empty
        if not isinstance(plan, list) or not plan:
            print("❌ No plan found in memory. Please generate a plan first using the 'plan' command.")
            if isinstance(plan, str): # If it's the default error string from recall
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
            # Use shlex to correctly parse the command string from the plan
            parts = shlex.split(command_string)
            if not parts: # If shlex.split results in an empty list (e.g., command_string was "")
                print(f"   └─ Skipping empty command in plan (Step {i}).")
                continue # Skip to the next command in the plan

            command_name = parts[0].lower()
            cmd_args = parts[1:]

            # Execute the command and get its result
            # This assumes command_manager.execute() is modified to return handler results
            execution_result = command_manager.execute(command_name, cmd_args)

            return_code, stdout, stderr = 0, "", "" # Defaults
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
                        for arg_path in cmd_args: # Iterate through pytest arguments
                            if Path(arg_path).is_file() and arg_path.endswith(".py"): # Check if arg is a file and python
                                file_to_test = arg_path
                                break
                            elif Path(arg_path).is_dir(): # If it's a dir, pytest might run tests within it
                                # This heuristic could be improved, e.g. by looking for test files in that dir
                                # For now, we can't reliably pick a single file to fix if a dir is given.
                                pass # Or try to find the most recently modified .py file in that dir

                    if file_to_test:
                        code_to_fix = utils.read_file(file_to_test)
                        if code_to_fix:
                            print(f"   └─ 🤖 LLM attempting to fix {file_to_test} based on error (first 300 chars):\n{current_error_log[:300]}...") 
                            fixed_code = agent.attempt_fix(code_to_fix, current_error_log)
                            print(f"   └─ Proposed fix by LLM for {file_to_test}:\n-------\n{fixed_code}\n-------")
                            
                            # More robust sanity check: ensure there's at least one non-comment, non-empty line
                            has_actual_code = any(line.strip() and not line.strip().startswith("#") for line in fixed_code.splitlines())
                            if fixed_code and has_actual_code:
                                utils.write_file(file_to_test, fixed_code)
                                print(f"   └─ ✨ Applied potential fix to {file_to_test}. Retrying tests...")
                                current_return_code, retry_stdout, retry_stderr = utils.execute_command(" ".join(cmd_args))
                                current_error_log = retry_stdout + retry_stderr # Update error log for next potential attempt

                                if current_return_code == 0:
                                    print("   └─ ✅ Self-correction successful! Tests now pass.")
                                    break # Exit the fix attempt loop
                                else:
                                    print(f"   └─ ❌ Self-correction attempt {attempt + 1} failed. Tests still failing.")
                                    if attempt + 1 == MAX_FIX_ATTEMPTS:
                                        print(f"      └─ Max fix attempts reached. Last error log:\n{current_error_log}")
                            else:
                                print(f"   └─ ⚠️ LLM did not provide a valid fix on attempt {attempt + 1}. Stopping self-correction for this step.")
                                break # Exit the fix attempt loop
                        else:
                            print(f"   └─ ⚠️ Could not read file {file_to_test} to attempt fix. Stopping self-correction.")
                            break # Exit the fix attempt loop
                    else:
                        print("   └─ ⚠️ Could not determine which file to fix for self-correction. Stopping.")
                        break # Exit the fix attempt loop
                else: # This 'else' belongs to the 'for' loop, executed if the loop completed without a 'break'
                    if current_return_code != 0: # Check if tests are still failing after all attempts
                        print("   └─ ❌ Self-correction ultimately failed after all attempts.")
                        
        print("\n✅ Plan execution complete.")

    register("plan", handle_plan, "Creates a multi-step plan to achieve a goal.")
    register("execute", handle_execute, "Executes the most recently created plan.")

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
            elif len(args) == 2: # Get all preferences in a category
                category_name = args[1]
                category_data = user_profile.data.get(category_name) # Access data directly
                if category_data is not None: # Check if category exists
                    if category_data: # Check if category is not empty
                        print(f"Preferences in category '{category_name}':")
                        for key, value_item in category_data.items(): # Renamed value to value_item
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

    # Feedback Command
    def handle_feedback(args):
        if not args or args[0].lower() not in ['good', 'bad', 'ok', 'positive', 'negative', 'neutral']:
            print("Usage: feedback <good|bad|ok> [optional comment]")
            print("Example: feedback good Loved the creativity!")
            return

        rating_map = {
            "good": "positive", "positive": "positive",
            "bad": "negative", "negative": "negative",
            "ok": "neutral", "neutral": "neutral"
        }
        rating = rating_map.get(args[0].lower())
        comment = " ".join(args[1:]) if len(args) > 1 else ""

        last_interaction = memory.recall('last_ai_interaction')
        user_profile.add_feedback(rating, comment, context=last_interaction)
        memory.remember('last_ai_interaction', None) # Clear after feedback is given

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
            trigger_phrase = " ".join(args[2:]) if len(args) > 2 else None # Assumes trigger phrase is the rest
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
                skill_filepath = SkillManager.SKILLS_DIR / skill_filename # Use SKILLS_DIR from SkillManager
                if utils.write_file(str(skill_filepath.relative_to(utils.WORKSPACE_DIR)), generated_skill_code): # write_file expects relative path
                    print(f"✅ Skill '{new_skill_name}' saved to {skill_filepath}")
                    skill_manager.refresh_skills() # Auto-refresh to load the new skill
                else:
                    print(f"❌ Failed to save skill '{new_skill_name}'.")
            else:
                print("Skill creation cancelled.")
        else:
            print(f"Unknown skills action: '{action}'. Valid actions: list, refresh, create_from_plan.")
    register("skills", handle_skills, "Manages and lists available agent skills.")

    # Helper function for suggesting and creating skills from patterns
    def _proactively_suggest_skill_creation_from_patterns(analyzed_patterns):
        if not analyzed_patterns:
            return

        # For proactive suggestion, maybe only consider the top pattern or a few
        # For simplicity, let's work with the first (most frequent/longest) pattern
        top_pattern_sequence, top_pattern_count = analyzed_patterns[0]

        print(f"\n[Proactive Suggestion] I've noticed a recurring pattern: `{' -> '.join(top_pattern_sequence)}` (used {top_pattern_count} times).")
        create_skill_q = input("Would you like to try creating a skill from this pattern? (y/n): ").lower()
        
        if create_skill_q == 'y':
            chosen_sequence_list = list(top_pattern_sequence)
            skill_name_suggestion = f"Auto{chosen_sequence_list[0].capitalize()}{chosen_sequence_list[1].capitalize() if len(chosen_sequence_list) > 1 else ''}Skill"
            new_skill_name = input(f"Enter a name for the new skill (default: {skill_name_suggestion}): ") or skill_name_suggestion
            trigger_phrase = input(f"Enter an optional trigger phrase for '{new_skill_name}' (e.g., \"perform my common task\"): ") or None
            
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
            else:
                print("Skill creation from pattern cancelled.")

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
            # Parameters for analysis could be added as args later
            patterns = pattern_analyzer.analyze_command_history()
            if patterns:
                print("\n--- Potential Skill Candidates (Frequent Command Sequences) ---")
                for seq, count in patterns:
                    print(f"  - Sequence: {', '.join(seq)} (Occurred {count} times)")
                print("-------------------------------------------------------------\n")
                # Call the refactored suggestion logic
                _proactively_suggest_skill_creation_from_patterns(patterns)
            # Message if no patterns found is handled by analyze_command_history itself

    register("history", handle_history, "Views command history.")
    # --- Load Plugins ---
    plugin_manager.discover_plugins()
    for plugin in plugin_manager.plugins:
        plugin.register_commands(command_manager)

    # DEBUG: Print all registered commands before starting the loop
    print("\n[DEBUG] Registered commands before main loop:")
    if command_manager.commands:
        for cmd_name in sorted(command_manager.commands.keys()):
            print(f"  - {cmd_name}")
    else:
        print("  - No commands registered in CommandManager.")
    print("[DEBUG] End of registered commands list.\n")

    print("🧠 The Giblet is awake. All commands registered. Type 'help' for a list of commands.")
    
    command_execution_count = 0
    PROACTIVE_ANALYSIS_THRESHOLD = 5 # Analyze patterns every N commands

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
            command_execution_count += 1

            if command_execution_count % PROACTIVE_ANALYSIS_THRESHOLD == 0:
                # print("\n[Proactive Check] Analyzing command history for patterns...") # Optional: can be noisy
                # Use a higher min_occurrences for proactive suggestions to reduce noise
                patterns = pattern_analyzer.analyze_command_history(min_len=2, max_len=3, min_occurrences=3) 
                if patterns:
                    _proactively_suggest_skill_creation_from_patterns(patterns)

        except KeyboardInterrupt:
            print("\n🧠 Going to sleep. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            logging.exception("An unhandled exception occurred in the CLI loop.")