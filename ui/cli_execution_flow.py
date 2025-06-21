# ui/cli_execution_flow.py
import shlex
from pathlib import Path

from core import utils
from core.memory import Memory
from core.agent import Agent
from core.command_manager import CommandManager

MAX_FIX_ATTEMPTS = 3 # Define this constant here, as it's used in this module

def execute_plan_with_self_correction(
    plan: list[str],
    memory: Memory,
    command_manager: CommandManager,
    agent: Agent
):
    """
    Executes a given plan, including self-correction logic for test failures.

    Args:
        plan (list[str]): A list of command strings to execute.
        memory (Memory): The memory system for recalling/remembering data.
        command_manager (CommandManager): The command manager to execute commands.
        agent (Agent): The agent instance for self-correction.
    """
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