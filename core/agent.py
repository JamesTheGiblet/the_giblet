# core/agent.py
import json
from core.idea_synth import IdeaSynthesizer # <<< CHANGED: Import the correct module
from core.code_generator import CodeGenerator # <<< NEW IMPORT
from core.skill_manager import SkillManager # <<< NEW IMPORT
from pathlib import Path # For reading the skill creation guide

class Agent:
    def __init__(self, idea_synth: IdeaSynthesizer, code_generator: CodeGenerator, skill_manager: SkillManager): # <<< Add SkillManager
        """Initializes the Autonomous Agent."""
        self.idea_synth = idea_synth # <<< CHANGED
        self.code_generator = code_generator # <<< NEW
        self.skill_manager = skill_manager # <<< Store SkillManager
        if self.idea_synth.model and self.code_generator.model:
            print("🤖 Autonomous Agent initialized with LLM connections.")
        else:
             print("🤖 Autonomous Agent could not initialize (missing LLM connection).")
        
        # Load skill creation guide content
        self.skill_creation_guide_content = ""
        try:
            guide_path = Path(__file__).parent.parent / "SKILL_CREATION_GUIDE.md"
            self.skill_creation_guide_content = guide_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Could not load SKILL_CREATION_GUIDE.md: {e}")

    def create_plan(self, high_level_goal: str) -> list[str]:
        """
        Takes a high-level goal and breaks it down into a list of Giblet commands.
        """
        if not self.idea_synth.model:
            return ["# Agent is not available."]

        print(f"🤖 Decomposing goal into a multi-step plan: '{high_level_goal}'...")

        available_skills = self.skill_manager.list_skills()
        skills_prompt_text = "No specific skills available."
        if available_skills:
            skills_prompt_text = "Consider using these available skills if they match the goal or sub-tasks:\n"
            for skill_info in available_skills:
                skills_prompt_text += f"- Skill Name: \"{skill_info['name']}\"\n  Description: {skill_info['description']}\n"
                # Future: Add skill_info['parameters_needed'] to the prompt

        final_prompt = f"""
        You are an expert software architect and project planner. Your task is to take a high-level user goal and break it down into a precise, ordered sequence of Giblet CLI commands.

        The user's goal is: "{high_level_goal}"

        You must respond with ONLY a valid JSON array of strings. Each string in the array must be a complete, executable Giblet command or a skill invocation.
        A skill invocation looks like: `skill <SkillName> [param1=value1 param2="value with spaces" ...]`

        Available Giblet commands for your plan:
        - `write <filepath> "<file content description>"`
        - `generate function "<function description>"`
        - `generate tests <filepath>`
        - `refactor <filepath> "<refactoring instruction>"`
        - `exec "<shell_command>"`
        
        {skills_prompt_text}

        Example Response for a goal of "create a python script that prints hello world and then summarize it":
        [
            "skill HelloWorld name=User",
            "write main.py \\"a simple python script that prints 'hello world' to the console\\"",
            "exec python main.py",
            "skill SummarizeFile filepath=main.py"
        ]
        """

        try:
            # <<< CHANGED: Use the correct synthesizer instance
            response_text = self.idea_synth.generate_text(final_prompt)

            json_response = response_text.strip().replace("```json", "").replace("```", "")
            plan = json.loads(json_response)
            return plan
        except Exception as e:
            print(f"❌ An error occurred during planning: {e}")
            return [f"# Failed to generate a valid plan: {e}"]

    # <<< NEW METHOD
    def attempt_fix(self, source_code: str, error_log: str) -> str:
        """
        Takes source code and a test error, and asks the LLM for a fix.
        """
        if not self.code_generator.model: # Check code_generator's model
            return f"# Agent's CodeGenerator is not available."

        print("🤖 Test failure detected. Attempting self-correction...")

        final_prompt = f"""
        You are an expert Python debugger. The following source code is failing its unit tests.
        Your task is to analyze the source code and the provided test failure log, identify the bug, and return a corrected version of the full source code.

        Only return the complete, corrected Python code in a single markdown code block. Do not include any explanatory text.

        Failed Test Log:
        ```
        {error_log}
        ```

        Source Code to Fix:
        ```python
        {source_code}
        ```
        """

        # We can use the CodeGenerator's method for this structured response
        return self.code_generator.generate_text(final_prompt)

    def generate_skill_from_plan(self, plan_steps: list[str], new_skill_name: str, trigger_phrase: str | None = None) -> str:
        """
        Uses the LLM to generate Python code for a new skill based on a list of plan steps.
        """
        if not self.code_generator.model:
            return "# CodeGenerator model not available. Cannot generate skill."

        print(f"🤖 Generating skill code for '{new_skill_name}' based on recent plan...")

        plan_steps_formatted = "\n".join([f"    - Step: `giblet {step}`" for step in plan_steps])

        # Instruction for can_handle
        can_handle_instruction = f"The 'can_handle' method should effectively determine if the skill is suitable for a given goal. It should ideally return True if the `goal_description` contains a key phrase like: '{trigger_phrase}'."
        if not trigger_phrase:
            can_handle_instruction = "For the 'can_handle' method, analyze the plan's overall purpose to infer a suitable trigger phrase. For example, if the plan involves writing a file and then testing it, a trigger phrase might be 'create and test file'. If the purpose is very general, make the trigger phrase reflect that, or use a broader keyword."

        # Instruction for get_parameters_needed
        parameters_instruction = """
        For 'get_parameters_needed', meticulously analyze the plan steps.
        1. Identify any values (filenames, numbers, strings, paths) that appear to be specific instances rather than fixed parts of the skill's logic. These should become parameters to make the skill reusable.
        2. For each identified parameter, define its 'name', a clear 'description', its likely 'type' (e.g., 'str', 'int', 'bool', 'filepath'), and whether it's 'required'.
        3. If a value in the plan seems like a common default, consider making the parameter optional (`required: False`) and use this default in the `execute` method if the parameter isn't provided.
        4. If no parts of the plan seem variable or suitable for parameterization, return an empty list `[]`.
        Example: If a plan step is `write report.txt "Initial report content"`, 'report.txt' could be a parameter `{"name": "filename", "description": "The name of the file to write", "type": "str", "required": True}`.
        The 'execute' method would then use `params.get("filename")`.
        """
        # Instruction for execute method
        execute_instruction = "The `execute` method is the core of the skill. It must use `self.command_manager.execute(command_name, args_list)` to run the Giblet commands derived from the plan. If you defined parameters in `get_parameters_needed`, ensure the `execute` method correctly retrieves these parameters using `params.get('param_name')` and substitutes them into the command arguments. Strive to make the command execution within the skill flexible by using these parameters. Return True on success, False on failure, and include print statements for important actions or errors."

        final_prompt = f"""
        You are an expert Python programmer tasked with creating a new Skill class for 'The Giblet' system.
        The skill should encapsulate the following sequence of Giblet commands (the plan):
        {plan_steps_formatted}

        Adhere strictly to the following Skill Creation Guide:
        --- START SKILL CREATION GUIDE ---
        {self.skill_creation_guide_content}
        --- END SKILL CREATION GUIDE ---

        Specifically, you need to:
        1.  Create a Python class named `{new_skill_name}Skill` that inherits from `core.skill_manager.Skill`.
        2.  Set the `NAME` class attribute to "{new_skill_name}".
        3.  Write a concise `DESCRIPTION` for what this skill accomplishes based on the plan.
        4.  Implement the `can_handle(self, goal_description: str, context: dict) -> bool` method. {can_handle_instruction}
        5.  Implement the `get_parameters_needed(self) -> list[dict]` method, following these guidelines: {parameters_instruction}
        6.  Implement the `execute(self, goal_description: str, context: dict, **params) -> bool` method. {execute_instruction}

        Return ONLY the complete Python code for the new skill class, enclosed in a single markdown code block.
        Ensure all necessary imports (like `from core.skill_manager import Skill`) are included.
        """

        try:
            generated_code = self.code_generator.generate_text(final_prompt)
            return generated_code
        except Exception as e:
            print(f"❌ An error occurred during skill code generation: {e}")
            return f"# Error generating skill: {e}"