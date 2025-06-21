# core/agent.py

from core.idea_synth import IdeaSynthesizer
from core.code_generator import CodeGenerator
from core.skill_manager import SkillManager
import shlex
import json

class Agent:
    """
    The core agent that orchestrates idea synthesis, code generation,
    and skill execution to accomplish user goals.
    """
    def __init__(self, idea_synth: IdeaSynthesizer, code_generator: CodeGenerator, skill_manager: SkillManager):
        self.idea_synth = idea_synth
        self.code_generator = code_generator
        self.skill_manager = skill_manager

        # --- FIX APPLIED HERE ---
        # Standardizing the attribute name to `llm_provider` across all components.
        # The Agent will now correctly check for `self.idea_synth.llm_provider`.
        idea_synth_ready = self.idea_synth.llm_provider and self.idea_synth.llm_provider.is_available()
        code_gen_ready = self.code_generator.llm_provider and self.code_generator.llm_provider.is_available()

        if idea_synth_ready and code_gen_ready:
            print("[AGENT] Agent initialized and ready. All LLM-dependent components are available.")
        else:
            print("[AGENT] Agent initialized with limited functionality. One or more LLM components are not available.")

    def create_plan(self, goal: str) -> list[str]:
        """
        Creates a multi-step plan to achieve a goal using `giblet` commands.
        """
        prompt = f"""
        You are an expert software development agent.
        Create a sequence of `giblet` CLI commands to accomplish the following high-level goal.
        The plan should be a list of command-line strings. Do not number the steps.

        Available commands for planning:
        - `write <filepath>` (Writes user-provided content to a file. This is the first step for creating new code.)
        - `generate tests <filepath>` (Generates pytest tests for an existing file.)
        - `exec "<shell_command>"` (Executes a command like `pytest` or `python`.)
        - `read <filepath>`
        - `ls [directory]`

        **IMPORTANT**: To create a new script with code, you must first use the `write` command. The user will then be prompted to provide the code. After the code is written into a file, you can then generate tests for that file.

        Goal: "{goal}"

        Respond with ONLY the list of commands, one command per line.
        Example for creating and testing a script:
        write my_script.py
        generate tests my_script.py
        exec "pytest"
        """
        
        try:
            raw_plan = self.idea_synth.generate_text(prompt)
            plan_steps = [line.strip() for line in raw_plan.splitlines() if line.strip()]
            cleaned_steps = [step.replace("giblet ", "", 1) for step in plan_steps]
            return cleaned_steps
        except Exception as e:
            return [f"Failed to generate plan: {e}"]

    def attempt_fix(self, code_to_fix: str, error_log: str) -> str:
        """
        Attempts to fix a piece of code based on an error log.
        """
        prompt = f"""
        You are an expert debugging agent.
        The following Python code failed with an error.
        Analyze the error log and the code, and provide a corrected version of the code.

        Error Log:
        ---
        {error_log}
        ---

        Code with Bug:
        ---
        {code_to_fix}
        ---

        Respond with ONLY the complete, corrected Python code block. Do not include explanations.
        """
        try:
            fixed_code = self.code_generator.generate_text(prompt)
            if fixed_code.startswith("```python"):
                fixed_code = fixed_code[len("```python"):].strip()
            if fixed_code.endswith("```"):
                fixed_code = fixed_code[:-len("```")].strip()
            return fixed_code
        except Exception as e:
            return f"# Failed to attempt fix: {e}\n{code_to_fix}"

    def generate_skill_from_plan(self, plan: list[str], skill_name: str, trigger_phrase: str = None) -> str:
        """
        Generates the Python code for a new Skill class based on an executed plan.
        """
        plan_steps_formatted = "\n".join([f"            # Step {i+1}: giblet {step}" for i, step in enumerate(plan)])
        
        handle_method_body_parts = []
        for i, step in enumerate(plan):
            parts = shlex.split(step)
            command_name = parts[0]
            args_list_str = json.dumps(parts[1:])
            
            handle_method_body_parts.append(f'        print(f"Executing step {i+1}: {step}")')
            handle_method_body_parts.append(f'        command_manager.execute("{command_name}", {args_list_str})')
        
        handle_method_body = "\n".join(handle_method_body_parts)

        can_handle_logic = "return False # Default: does not handle any input"
        if trigger_phrase:
            safe_trigger = json.dumps(trigger_phrase.lower())
            can_handle_logic = f"return {safe_trigger} in user_input.lower()"

        prompt = f"""
        You are an agent that writes skills for another agent.
        Based on the provided plan, generate the complete Python code for a new Skill class.
        The class name must be `{skill_name}` and it must inherit from `BaseSkill`.
        The `handle` method should execute the plan steps using `command_manager.execute()`.
        The `can_handle` method should check if the user input contains a specific trigger phrase.

        Plan Steps:
        {plan_steps_formatted}

        Trigger Phrase for can_handle(): "{trigger_phrase if trigger_phrase else 'None'}"

        Generate the complete Python code file now.
        """
        
        skill_code = self.code_generator.generate_text(prompt)

        if "class" not in skill_code or "def" not in skill_code:
            skill_code = f'''
from core.skill_manager import BaseSkill
import shlex
import json

class {skill_name}(BaseSkill):
    """
    A skill generated automatically to execute a multi-step plan.
    Plan:
{plan_steps_formatted}
    """
    def __init__(self):
        self.name = "{skill_name}"
        self.description = "A skill to automatically {skill_name.lower().replace('_', ' ')}."

    def can_handle(self, user_input: str, command_manager: any) -> bool:
        """
        Determines if the user's input triggers this skill.
        """
        {can_handle_logic}

    def handle(self, user_input: str, command_manager: any):
        """
        Executes the pre-defined plan of commands.
        """
        print(f"Executing skill: {self.name}")
{handle_method_body}
        print(f"Skill {self.name} finished.")

'''
        return skill_code.strip()
