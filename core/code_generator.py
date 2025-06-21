# core/code_generator.py
import logging # <<< NEW IMPORT
import json
from core.user_profile import UserProfile # Import UserProfile
from core.memory import Memory # Import Memory
from core.llm_provider_base import LLMProvider # Import LLMProvider
from core.llm_capabilities import LLMCapabilities # New import
from .project_contextualizer import ProjectContextualizer # Import ProjectContextualizer


class CodeGenerator:
    def __init__(self, user_profile: UserProfile,
                 memory_system: Memory,
                 llm_provider: LLMProvider,
                 project_contextualizer: ProjectContextualizer): # Added project_contextualizer
        """
        Initializes the CodeGenerator.
        """
        self.user_profile = user_profile # Store the user_profile instance
        self.memory = memory_system # Store the memory_system instance
        self.llm_provider = llm_provider
        self.capabilities = LLMCapabilities(provider=self.llm_provider, user_profile=self.user_profile)
        self.logger = logging.getLogger(__name__) # <<< ADDED LOGGER
        self.project_contextualizer = project_contextualizer # Store ProjectContextualizer

        if self.llm_provider and self.llm_provider.is_available():
            print(f"💻 Code Generator initialized using {self.llm_provider.PROVIDER_NAME} ({self.llm_provider.model_name}). Max output tokens: {self.capabilities.max_output_tokens}.")
        else:
            print(f"⚠️ Code Generator: LLM provider {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'} is not available.")

    def generate_function(self, prompt: str) -> str:
        """Generates a single, clean Python function from a prompt."""
        if not self.llm_provider or not self.llm_provider.is_available():
            return f"# Code Generator is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'})."

        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        preferred_quotes = self.user_profile.get_preference("coding_style", "quote_type", "double")
        indent_size = self.user_profile.get_preference("coding_style", "indent_size", "4")

        print(f"💻 Generating function for '{user_name}': '{prompt}' (with project context)...")

        project_context_summary = self.project_contextualizer.get_full_context()

        # A meta-prompt specifically designed to get clean code as a response
        final_prompt = f"""
        Project Context:
        {project_context_summary}
        User prompt: "Create a Python function that {prompt}"
        This function is for a user named {user_name}.

        You are an expert Python code generator.
        Your task is to generate a single, complete, and clean Python function that satisfies the user's prompt.
        The function MUST include:
        1. Type hints for all arguments and the return value.
        2. A clear and concise docstring explaining what it does.
        3. The function should be pure and not have side effects if possible.
        4. Adhere to these user-specific coding style preferences:
           - Use {preferred_quotes} quotes for strings.
           - Use an indent size of {indent_size} spaces.

        ONLY return the Python code for the function itself, enclosed in a single markdown code block (```python...```). Do not include any explanatory text before or after the code block.
        """

        try:
            response_text = self.llm_provider.generate_text(
                final_prompt,
                max_tokens=self.capabilities.max_output_tokens
            )
            # Clean up the response to extract only the code block
            code_block = response_text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            
            # Store the generated code with a context ID and other relevant info
            interaction_data = {
                "output": code_block,
                "context_id": "code_gen:function_from_prompt",
                "module": "CodeGenerator",
                "method": "generate_function",
                "prompt_summary": prompt[:100]
            }
            self.memory.remember('last_ai_interaction', interaction_data)
            self.logger.info(f"Generated code for function based on prompt: {prompt[:50]}...")
            return code_block
        except Exception as e:
            return f"# An error occurred during code generation: {e}"

    # <<< NEW METHOD
    def generate_streamlit_ui(self, source_code: str, source_filename: str) -> str:
        """Generates a Streamlit UI from a Python data class definition."""
        if not self.llm_provider or not self.llm_provider.is_available():
            return f"# Code Generator is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'})."

        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        ui_style_preference = self.user_profile.get_preference("ui_style", "streamlit_theme", "default")

        print(f"💻 Generating Streamlit UI for '{source_filename}' for {user_name} (theme hint: {ui_style_preference}, with project context)...")

        project_context_summary = self.project_contextualizer.get_full_context()

        final_prompt = f"""
        Project Context:
        {project_context_summary}
        You are an expert Streamlit UI generator.
        Your task is to generate a complete, runnable Streamlit script based on the provided Python code containing a data class.
        The user generating this is {user_name}. If they specified a theme preference like '{ui_style_preference}', consider it if applicable to Streamlit's capabilities.

        The generated script must:
        1. Import streamlit as st.
        2. Import the data class from the source file ('{source_filename}').
        3. Create a title for the web page.
        4. Use `st.form` to create a form.
        5. Inside the form, create an appropriate Streamlit input widget for each attribute of the data class (e.g., `st.text_input` for `str`, `st.number_input` for `int`/`float`, `st.checkbox` for `bool`).
        6. Include a `st.form_submit_button`.
        7. If the form is submitted, it should instantiate the data class with the form data and display the resulting object using `st.success` and `st.json`.

        ONLY return the Python code for the Streamlit app, enclosed in a single markdown code block. Do not include any explanatory text.

        Here is the source code to analyze:
        ```python
        {source_code}
        ```
        """

        try:
            response_text = self.llm_provider.generate_text(
                final_prompt,
                max_tokens=self.capabilities.max_output_tokens
            )
            # Clean up the response to extract only the code block
            code_block = response_text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            self.memory.remember('last_ai_interaction', {
                "module": "CodeGenerator",
                "method": "generate_streamlit_ui",
                "prompt_summary": source_filename,
                "output_summary": code_block[:150]
            })
            return code_block
        except Exception as e:
            return f"# An error occurred during UI generation: {e}"

    # <<< NEW METHOD
    def refactor_code(self, source_code: str, instruction: str) -> dict:
        """Refactors a block of code based on a specific instruction."""
        if not self.llm_provider or not self.llm_provider.is_available():
            return {"refactored_code": f"# Code Generator is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'}).", "explanation": "LLM provider is not available."}

        user_name = self.user_profile.get_preference("general", "user_name", "the user")
        refactor_aggressiveness = self.user_profile.get_preference("coding_style", "refactor_aggressiveness", "moderate")

        print(f"💻 Refactoring code for {user_name} with instruction: '{instruction}' (aggressiveness: {refactor_aggressiveness}, with project context)...")

        project_context_summary = self.project_contextualizer.get_full_context()

        final_prompt = f"""
        Project Context:
        {project_context_summary}
        You are an expert Python code refactoring assistant. Your task is to rewrite the provided source code based on a specific instruction and explain your changes.
        Ensure the new code is clean, efficient, and maintains the original functionality.
        The user is {user_name}. Their preferred refactoring aggressiveness is '{refactor_aggressiveness}'.

        Refactoring Instruction: "{instruction}"
        Consider the user's preference for '{refactor_aggressiveness}' refactoring when applying changes.

        Source Code to Refactor:
        ```python
        {source_code}
        ```

        Respond with a JSON object containing two keys:
        1. "refactored_code": A string containing the complete, refactored Python code.
        2. "explanation": A string in Markdown format explaining the changes you made and why.

        ONLY return the raw JSON object. Do not include any explanatory text or markdown formatting around the JSON.
        """

        try:
            response_text = self.llm_provider.generate_text(
                final_prompt,
                max_tokens=self.capabilities.max_output_tokens
            )
            # Clean up the response to extract only the JSON block
            json_block = response_text.strip()
            if json_block.startswith("```json"):
                json_block = json_block[len("```json"):].strip()
            if json_block.endswith("```"):
                json_block = json_block[:-len("```")].strip()
            
            try:
                refactor_data = json.loads(json_block)
                if "refactored_code" in refactor_data and "explanation" in refactor_data:
                    self.memory.remember('last_ai_interaction', {
                        "module": "CodeGenerator", "method": "refactor_code",
                        "prompt_summary": instruction[:100],
                        "output_summary": refactor_data.get('refactored_code', '')[:150],
                        "explanation": refactor_data.get('explanation', '')[:150]
                    })
                    return refactor_data
                else:
                    return {"refactored_code": json_block, "explanation": "LLM did not return a valid JSON object with 'refactored_code' and 'explanation' keys."}
            except json.JSONDecodeError:
                return {"refactored_code": response_text, "explanation": "LLM did not return valid JSON. Displaying raw output as code."}

        except Exception as e:
            return {"refactored_code": f"# An error occurred during code refactoring: {e}", "explanation": str(e)}
         
    # <<< NEW METHOD
    def generate_unit_tests(self, source_code: str, source_filename: str) -> str:
        """Generates pytest unit tests for a given block of source code."""
        if not self.llm_provider or not self.llm_provider.is_available():
            return f"# Code Generator is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'})."

        print(f"🔬 Generating unit tests for '{source_filename}' using {self.llm_provider.PROVIDER_NAME} (with project context)...")

        project_context_summary = self.project_contextualizer.get_full_context()

        final_prompt = f"""
        Project Context:
        {project_context_summary}
        You are an expert Python test generator who uses the pytest framework.
        Your task is to write a comprehensive set of unit tests for the provided source code. 
        CRITICALLY IMPORTANT: The tests MUST verify the function's behavior based on its name and common programming conventions, NOT based on its current potentially flawed implementation. For example, a function named 'add' MUST be tested as if it performs addition (e.g., add(2,3) should be 5), regardless of what the provided source code currently does. A function named 'subtract' must be tested as if it performs subtraction.

        The generated test script must:
        1. Import pytest and the necessary modules from the source file.
        2. Include tests for edge cases and normal inputs, ensuring they validate the expected, correct behavior according to the function's implied purpose.
        3. For testing invalid inputs (e.g., wrong types that should cause an error in the function being tested), use `pytest.raises` to assert that the function *itself* raises the appropriate error. Do NOT write tests that expect an assertion about correct behavior to fail (e.g., do not use `pytest.raises(AssertionError)` to wrap a correct assertion).
        4. Follow standard pytest conventions, with test function names starting with `test_`.
        4. Be complete and runnable as-is.
        5. All generated tests should pass ONLY if the source code correctly implements the function's implied purpose (e.g., an 'add' function actually adds).
        6. Avoid generating tests that are designed to pass only if the function is implemented incorrectly. All tests should aim to validate the function's correctness based on its name and common usage.

        ONLY return the Python code for the test script, enclosed in a single markdown code block. Do not include any explanatory text before or after the code block.

        Source Code from '{source_filename}':
        ```python
        {source_code}
        ```
        """

        try:
            response_text = self.llm_provider.generate_text(
                final_prompt,
                max_tokens=self.capabilities.max_output_tokens
            )
            # Clean up the response to extract only the code block
            code_block = response_text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            self.memory.remember('last_ai_interaction', {
                "module": "CodeGenerator",
                "method": "generate_unit_tests",
                "prompt_summary": source_filename,
                "output_summary": code_block[:150]
            })
            return code_block
        except Exception as e:
            return f"# An error occurred during test generation: {e}"

    def generate_text(self, prompt: str) -> str:
        """
        Generates a direct text response from the model based on a given prompt,
        expecting a Python code block as the primary output.
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            return f"# Code Generator is not available (provider: {self.llm_provider.PROVIDER_NAME if self.llm_provider else 'None'})."

        print(f"💻 Generating text from prompt (expecting code) using {self.llm_provider.PROVIDER_NAME} (with project context)...")
        project_context_summary = self.project_contextualizer.get_full_context()

        final_prompt_with_context = f"""
        Project Context:
        {project_context_summary}
        {prompt}"""
        try:
            response_text = self.llm_provider.generate_text(
                final_prompt_with_context,
                max_tokens=self.capabilities.max_output_tokens
            )
            # Clean up the response to extract only the code block
            code_block = response_text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            self.memory.remember('last_ai_interaction', {
                "module": "CodeGenerator",
                "method": "generate_text", # Used by Agent's attempt_fix
                "prompt_summary": "LLM Fix Attempt" if "Source Code to Fix:" in prompt else prompt[:100],
                "output_summary": code_block[:150]
            })
            return code_block
        except Exception as e:
            # Consider logging the full exception 'e' here for debugging
            return f"# An error occurred during text generation: {e}"