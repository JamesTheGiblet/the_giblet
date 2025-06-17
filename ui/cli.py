# ui/cli.py
from core import utils
from core.memory import Memory
from core.roadmap_manager import RoadmapManager
from core.automator import Automator
from core.idea_synth import IdeaSynthesizer # <<< NEW IMPORT
from core.git_analyzer import GitAnalyzer # <<< NEW IMPORT
import logging # <<< NEW IMPORT

def print_help():
    """Prints the available commands and their usage."""
    print("\n--- The Giblet CLI ---")
    
    # <<< NEW SECTION
    print("\nCreative Commands:")
    print("  idea \"<prompt>\"          - Brainstorms practical ideas for a prompt.")
    print("  idea --weird \"<prompt>\"  - Brainstorms weird and unconventional ideas.")

    # <<< NEW SECTION
    print("\nGit Commands:")
    print("  git status             - Shows if there are uncommitted changes.")
    print("  git branches           - Lists all local branches.")
    print("  git log                - Shows the 5 most recent commit messages.")
    print("  git summary            - Generates an AI summary of recent commits.") # <<< NEW
    # <<< NEW SECTION
    print("\nWorkflow Commands:")
    print("  focus \"<your task>\"      - Sets your current task focus in the session.")
    print("  focus --clear              - Clears your current focus.")
    print("  automate stubs <filepath>  - Adds TODO stubs to empty functions in a file.")
    print("  automate changelog         - Generates a changelog from git history.") # <<< NEW

    # <<< NEW SECTION
    print("\nProject Commands:")
    print("  roadmap                - Displays the parsed project roadmap.")
    print("  roadmap done \"<desc>\"  - Marks a task as complete using its description.")

    print("\nFile Commands:")
    print("  read <filepath>        - Reads and prints the content of a file.")
    print("  write <filepath>       - Writes content to a file. You'll be prompted for the content.")
    print("  ls [directory]         - Lists files in the specified directory (or current if none).")
    print("  exec <command>         - Executes a shell command.")
    
    print("\nMemory Commands:")
    print("  remember <key> <value> - Saves a thought to this session's memory.")
    print("  recall <key>           - Recalls a thought from this session's memory.")
    print("  commit <key> <value>   - Commits a thought to long-term memory (saves to disk).")
    print("  retrieve <key>         - Retrieves a thought from long-term memory.")
    print("  checkpoint save <name> - Saves the current session to a checkpoint.")
    print("  checkpoint load <name> - Loads a checkpoint into the current session.")

    print("\nSystem Commands:")
    print("  help                   - Shows this help message.")
    print("  exit / quit            - Exits the interactive session.")
    print("----------------------\n")

def start_cli_loop():
    """Starts the main interactive loop for The Giblet."""
    memory = Memory()
    roadmap_manager = RoadmapManager(memory_system=memory)
    idea_synth = IdeaSynthesizer() # <<< NEW: Initialize the Idea Synthesizer
    automator = Automator() # <<< NEW
    git_analyzer = GitAnalyzer() # <<< NEW
    print("🧠 The Giblet is awake. Type 'help' for a list of commands.")
    
    while True:
        try:
            # <<< DYNAMIC PROMPT LOGIC
            # Priority 1: Check for a manual user-set focus.
            manual_focus = memory.recall("current_focus")
            if manual_focus:
                # Truncate for display if too long
                display_focus = (manual_focus[:20] + '...') if len(manual_focus) > 23 else manual_focus
                prompt = f" giblet [focus: {display_focus}]> "
            # Priority 2: If no manual focus, check for a git branch.
            elif git_analyzer.repo: # Check if git_analyzer successfully initialized a repo
                branch_name = git_analyzer.repo.active_branch.name
                prompt = f" giblet [branch: {branch_name}]> "
            # Priority 3: Default prompt if neither is available.
            else:
                prompt = " giblet> "

            user_input = input(prompt).strip()
            
            if not user_input:
                continue

            parts = user_input.split(maxsplit=2)
            command = parts[0].lower()
            arg1 = parts[1] if len(parts) > 1 else ""
            arg2 = parts[2] if len(parts) > 2 else ""

            if command in ["exit", "quit"]:
                print("🧠 Going to sleep. Goodbye!")
                break
            
            elif command == "help":
                print_help()

            # <<< NEW: Focus command block
            elif command == "focus":
                if arg1 == "--clear":
                    memory.remember("current_focus", None) # Store None to signify no focus
                    print("🌀 Focus cleared.")
                elif arg1: # If there's any argument after "focus" (and it's not --clear)
                    # The prompt text is everything after "focus "
                    focus_text = user_input[len(command):].strip().strip('"')
                    memory.remember("current_focus", focus_text)
                    print(f"🌀 OK. Focusing on: \"{focus_text}\"")
                else: # Just "focus" was typed
                    current_focus_val = memory.recall("current_focus") # Re-fetch in case it was just cleared
                    print(f"Your current focus is: \"{current_focus_val}\"") if current_focus_val else print("No focus is set. Use 'focus \"<your task>\"'.")

            # <<< NEW: Idea command block
            elif command == "idea":
                if not arg1:
                    print("Usage: idea \"<prompt>\" or idea --weird \"<prompt>\"")
                else:
                    weird_mode = False
                    # Get the full text after "idea" command itself
                    prompt_text = user_input[len(command):].strip()
                    
                    if arg1 == "--weird":
                        weird_mode = True
                        # Remove "--weird" from the prompt_text
                        prompt_text = prompt_text[len("--weird"):].strip()

                    if not prompt_text:
                        print("A prompt is required. Usage: idea \"<your prompt>\" or idea --weird \"<your prompt>\"")
                    else:
                        # Strip quotes for cleanliness if user included them around the whole prompt
                        response = idea_synth.generate_ideas(prompt_text.strip('"'), weird_mode=weird_mode)
                        print("\n--- Giblet's Ideas ---")
                        print(response)
                        print("----------------------\n")

            # --- Roadmap Commands ---
            elif command == "roadmap":
                if arg1 == "done":
                    if not arg2:
                        print("Usage: roadmap done \"<task description>\"")
                    else:
                        # Strip quotes if user included them
                        roadmap_manager.complete_task(arg2.strip('"'))
                elif not arg1: # No subcommand, just "roadmap"
                    roadmap_manager.view_roadmap()
                else:
                    print(f"Unknown roadmap command: '{arg1}'. Try 'roadmap done \"<description>\"' or just 'roadmap'.")

            # <<< NEW: Git command block
            elif command == "git":
                if arg1 == "status":
                    print(f"👁️  Branch Status: {git_analyzer.get_branch_status()}")
                elif arg1 == "branches":
                    branches = git_analyzer.list_branches()
                    print("👁️  Available branches:\n - " + "\n - ".join(branches))
                elif arg1 == "log":
                    log = git_analyzer.get_commit_log()
                    print("👁️  Recent Commits:")
                    for commit in log:
                        print(f"  - [{commit['date']}] {commit['sha']} - {commit['message']} ({commit['author']})")
                # <<< NEW
                elif arg1 == "summary":
                    summary = git_analyzer.summarize_recent_activity(idea_synth)
                    print("\n--- AI Summary of Recent Activity ---")
                    print(summary)
                    print("-------------------------------------\n")
                else:
                    print("Unknown git command. Try 'status', 'branches', 'log', or 'summary'.")
            # <<< NEW: Automate command block
            elif command == "automate":
                if arg1 == "stubs":
                    if not arg2: print("Usage: automate stubs <filepath>")
                    else: automator.generate_stubs(arg2)
                elif arg1 == "changelog":
                    automator.generate_changelog()
                else:
                    print(f"Unknown automate command: '{arg1}'. Try 'stubs' or 'changelog'.")
            
            # --- Checkpoint Commands ---
            elif command == "checkpoint":
                if arg1 == "save":
                    if not arg2: print("Usage: checkpoint save <name>")
                    else: memory.save_checkpoint(arg2)
                elif arg1 == "load":
                    if not arg2: print("Usage: checkpoint load <name>")
                    else: memory.load_checkpoint(arg2)
                else:
                    print(f"Unknown checkpoint command: '{arg1}'. Try 'save' or 'load'.")


            # --- File Commands ---
            elif command == "read":
                if not arg1: print("Usage: read <filepath>")
                else:
                    content = utils.read_file(arg1)
                    if content is not None: print(f"\n--- File Content ---\n{content}\n--------------------\n")
            elif command == "write":
                if not arg1: print("Usage: write <filepath>")
                else:
                    print("Enter content to write. Type 'EOF' on a new line to finish.")
                    lines = []
                    while True:
                        line = input()
                        if line == "EOF": break
                        lines.append(line)
                    utils.write_file(arg1, "\n".join(lines))
            elif command == "ls":
                files = utils.list_files(arg1 or ".")
                print("\n--- File List ---\n" + "\n".join(files) + "\n-----------------\n")
            elif command == "exec":
                if not arg1: print("Usage: exec <command>")
                else:
                    code, out, err = utils.execute_command(arg1)
                    print(f"\n--- Command Output (Code: {code}) ---")
                    if out: print(f"[stdout]:\n{out}")
                    if err: print(f"[stderr]:\n{err}")
                    print("---------------------------------\n")

            # --- Memory Commands ---
            elif command == "remember":
                if not arg1 or not arg2: print("Usage: remember <key> <value>")
                else:
                    memory.remember(arg1, arg2)
                    print(f"🧠 OK. I'll remember '{arg1}' for this session.")
            elif command == "recall":
                if not arg1: print("Usage: recall <key>")
                else:
                    value = memory.recall(arg1)
                    print(f"🔎 Recalling '{arg1}': {value if value is not None else 'Not found in session memory.'}")
            elif command == "commit":
                if not arg1 or not arg2: print("Usage: commit <key> <value>")
                else:
                    memory.commit(arg1, arg2)
                    print(f"💾 OK. I've committed '{arg1}' to long-term memory.")
            elif command == "retrieve":
                if not arg1: print("Usage: retrieve <key>")
                else:
                    value = memory.retrieve(arg1)
                    print(f"🔎 Retrieving '{arg1}': {value if value is not None else 'Not found in long-term memory.'}")
            elif command == "save":
                memory.save_to_disk()

            # Add this temporarily for testing
            elif command == "crashme":
                raise ValueError("This is a deliberate test crash.")

            else:
                print(f"Unknown command: '{command}'. Type 'help' for options.")

        except KeyboardInterrupt:
            print("\n🧠 Going to sleep. Goodbye!")
            break
        except Exception as e:
            # <<< UPDATED: The new error handling logic
            print(f"\n❌ An unexpected error occurred: {e}")
            print("   A detailed traceback has been saved to 'data/giblet_debug.log'.")
            logging.exception("An unhandled exception occurred in the CLI loop.")