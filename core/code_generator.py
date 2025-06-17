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

    def generate_text(self, prompt: str) -> str:
        """
        Generates a direct text response from the model based on a given prompt,
        expecting a Python code block as the primary output.
        """
        if not self.model:
            return "# Code Generator is not available."

        print(f"💻 Generating text from prompt (expecting code)...")
        try:
            response = self.model.generate_content(prompt)
            # Clean up the response to extract only the code block
            code_block = response.text.strip()
            if code_block.startswith("```python"):
                code_block = code_block[len("```python"):].strip()
            if code_block.endswith("```"):
                code_block = code_block[:-len("```")].strip()
            return code_block
        except Exception as e:
            # Consider logging the full exception 'e' here for debugging
            return f"# An error occurred during text generation: {e}"