# core/agent.py
import json
from core.idea_synth import IdeaSynthesizer # <<< CHANGED: Import the correct module
from core.code_generator import CodeGenerator # <<< NEW IMPORT

class Agent:
    def __init__(self, idea_synth: IdeaSynthesizer, code_generator: CodeGenerator): # <<< CHANGED: Accept instances
        """Initializes the Autonomous Agent."""
        self.idea_synth = idea_synth # <<< CHANGED
        self.code_generator = code_generator # <<< NEW
        if self.idea_synth.model and self.code_generator.model:
            print("🤖 Autonomous Agent initialized with LLM connections.")
        else:
             print("🤖 Autonomous Agent could not initialize (missing LLM connection).")

    def create_plan(self, high_level_goal: str) -> list[str]:
        """
        Takes a high-level goal and breaks it down into a list of Giblet commands.
        """
        if not self.idea_synth.model:
            return ["# Agent is not available."]

        print(f"🤖 Decomposing goal into a multi-step plan: '{high_level_goal}'...")

        final_prompt = f"""
        You are an expert software architect and project planner. Your task is to take a high-level user goal and break it down into a precise, ordered sequence of Giblet CLI commands.

        The user's goal is: "{high_level_goal}"

        You must respond with ONLY a valid JSON array of strings. Each string in the array must be a complete, executable Giblet command.

        Available Giblet commands for your plan:
        - `write <filepath> "<file content description>"`
        - `generate function "<function description>"`
        - `generate tests <filepath>`
        - `refactor <filepath> "<refactoring instruction>"`
        - `exec "<shell_command>"`

        Example Response for a goal of "create a python script that prints hello world":
        [
            "write main.py \\"a simple python script that prints 'hello world' to the console\\"",
            "exec python main.py"
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