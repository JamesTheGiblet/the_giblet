# core/code_generator.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

class CodeGenerator:
    def __init__(self):
        """Initializes the connection to the generative AI model for code generation."""
        self.model = None
        try:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found.")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            print("💻 Code Generator initialized with Gemini-1.5-Flash.")
        except Exception as e:
            print(f"❌ Failed to initialize Code Generator: {e}")

    def generate_function(self, prompt: str) -> str:
        """Generates a single, clean Python function from a prompt."""
        if not self.model:
            return "# Code Generator is not available."

        print(f"💻 Generating function for: '{prompt}'...")

        # A meta-prompt specifically designed to get clean code as a response
        final_prompt = f"""
        User prompt: "Create a Python function that {prompt}"

        You are an expert Python code generator.
        Your task is to generate a single, complete, and clean Python function that satisfies the user's prompt.
        The function MUST include:
        1. Type hints for all arguments and the return value.
        2. A clear and concise docstring explaining what it does.
        3. The function should be pure and not have side effects if possible.

        ONLY return the Python code for the function itself, enclosed in a single markdown code block (```python...```). Do not include any explanatory text before or after the code block.
        """

        try:
            response = self.model.generate_content(final_prompt)
            # Clean up the response to extract only the code block
            code_block = response.text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            return code_block
        except Exception as e:
            return f"# An error occurred during code generation: {e}"

    # <<< NEW METHOD
    def generate_streamlit_ui(self, source_code: str, source_filename: str) -> str:
        """Generates a Streamlit UI from a Python data class definition."""
        if not self.model:
            return "# Code Generator is not available."

        print(f"💻 Generating Streamlit UI for '{source_filename}'...")

        final_prompt = f"""
        You are an expert Streamlit UI generator.
        Your task is to generate a complete, runnable Streamlit script based on the provided Python code containing a data class.

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
            response = self.model.generate_content(final_prompt)
            # Clean up the response to extract only the code block
            code_block = response.text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            return code_block
        except Exception as e:
            return f"# An error occurred during UI generation: {e}"

    # <<< NEW METHOD
    def refactor_code(self, source_code: str, instruction: str) -> str:
        """Refactors a block of code based on a specific instruction."""
        if not self.model:
            return f"# Code Generator is not available."

        print(f"💻 Refactoring code with instruction: '{instruction}'...")

        final_prompt = f"""
        You are an expert Python code refactoring assistant.
        Your task is to rewrite the provided source code based on a specific instruction.
        Ensure the new code is clean, efficient, and maintains the original functionality.
        ONLY return the new, complete source code in a single markdown code block. Do not add any explanatory text.

        Refactoring Instruction: "{instruction}"

        Source Code to Refactor:
        ```python
        {source_code}
        ```
        """

        try:
            response = self.model.generate_content(final_prompt)
            # Clean up the response to extract only the code block
            code_block = response.text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            return code_block
        except Exception as e:
            return f"# An error occurred during code refactoring: {e}"
        
    # <<< NEW METHOD
    def generate_unit_tests(self, source_code: str, source_filename: str) -> str:
        """Generates pytest unit tests for a given block of source code."""
        if not self.model:
            return "# Code Generator is not available."

        print(f"🔬 Generating unit tests for '{source_filename}'...")

        final_prompt = f"""
        You are an expert Python test generator who uses the pytest framework.
        Your task is to write a comprehensive set of unit tests for the provided source code.

        The generated test script must:
        1. Import pytest and the necessary modules from the source file.
        2. Include tests for edge cases, normal inputs, and expected failures (e.g., using `pytest.raises`).
        3. Follow standard pytest conventions, with test function names starting with `test_`.
        4. Be complete and runnable as-is.

        ONLY return the Python code for the test script, enclosed in a single markdown code block. Do not include any explanatory text.

        Source Code from '{source_filename}':
        ```python
        {source_code}
        ```
        """

        try:
            response = self.model.generate_content(final_prompt)
            # Clean up the response to extract only the code block
            code_block = response.text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            return code_block
        except Exception as e:
            return f"# An error occurred during test generation: {e}"