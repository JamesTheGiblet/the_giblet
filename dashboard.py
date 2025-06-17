# dashboard.py
import streamlit as st
import httpx
import sys
import difflib # <<< NEW IMPORT at the top
from pathlib import Path

# This line ensures that the script can find your 'core' modules
sys.path.append(str(Path(__file__).parent))

from core.roadmap_manager import RoadmapManager
from core.git_analyzer import GitAnalyzer
from core.idea_synth import IdeaSynthesizer
from core.memory import Memory

# Function to sanitize strings for display, especially on Windows with 'charmap' issues
def sanitize_for_display(text: str) -> str:
    """
    Sanitizes a string by attempting to encode and decode it using 'charmap'
    with replacements for unmappable characters. This helps prevent
    UnicodeEncodeError on systems/consoles with limited encodings like 'charmap'.
    """
    if not isinstance(text, str):
        return str(text) # Ensure we're working with a string
    try:
        # Encode to 'charmap', replacing unmappable characters, then decode back to string.
        return text.encode('charmap', 'replace').decode('charmap')
    except Exception:
        # Fallback if 'charmap' processing itself fails for some reason
        return text.encode('utf-8', 'replace').decode('utf-8')

def main():
    """
    The main function for the Streamlit dashboard.
    """
    st.set_page_config(
        page_title="The Giblet Dashboard",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 The Giblet: Project Cockpit")

    # <<< UPDATED: Add a new tab for the refactor tool
    tabs = st.tabs(["🗺️ Roadmap", "📜 History", "🛠️ Generator", "✨ Refactor", "📂 File Explorer", "🤖 Automation"])

    with tabs[0]:
        st.header("Project Roadmap")
        try:
            # The roadmap tab now calls the API
            response = httpx.get("http://localhost:8000/roadmap", timeout=10)
            response.raise_for_status()
            data = response.json()
            tasks = data.get("roadmap", [])

            # <<< FIX: This display logic is now correctly indented inside the 'try' block.
            if not tasks:
                st.warning("No tasks found in roadmap.md")
            else:
                phases = {}
                current_phase = "General Tasks"
                for task in tasks:
                    if 'Phase' in task['description']:
                        current_phase = task['description']
                        if current_phase not in phases:
                            phases[current_phase] = []
                    else:
                        if current_phase not in phases:
                            phases[current_phase] = []
                        phases[current_phase].append(task)
                
                for phase_name, phase_tasks in phases.items():
                    with st.expander(f"**{sanitize_for_display(phase_name)}**", expanded=True):
                        for task in phase_tasks:
                            is_complete = (task['status'] == 'complete')
                            st.checkbox(sanitize_for_display(task['description']), value=is_complete, disabled=True)

        except httpx.RequestError:
            st.error("Could not connect to The Giblet API. Is the server running?")
        except Exception as e:
            st.error(f"Error in Roadmap tab: {sanitize_for_display(str(e))}")
    with tabs[1]:
        st.header("Recent Project History")
        try:
            # This logic now correctly initializes the GitAnalyzer inside the try block
            git_analyzer = GitAnalyzer()
            if not git_analyzer.repo:
                st.warning("Not a Git repository. History cannot be displayed.")
            else:
                # <<< FIX: This display logic is now correctly indented inside the 'try' block.
                log = git_analyzer.get_commit_log(max_count=15)
                if not log:
                    st.warning("No Git history found.")
                else:
                    for commit in log:
                        sha = commit.get('sha', 'N/A')
                        author = sanitize_for_display(commit.get('author', 'N/A'))
                        date = commit.get('date', 'N/A') # Dates are typically ASCII-safe
                        message = sanitize_for_display(commit.get('message', 'N/A'))

                        st.markdown(f"**Commit:** `{sha}`")
                        st.text(f"Author: {author} | Date: {date}")
                        st.info(f"{message}", icon="💬")
                        st.divider()
        except Exception as e:
            st.error(f"Could not load Git history: {sanitize_for_display(str(e))}")
    with tabs[2]:
        # The Generator tab requires its own instances
        try:
            idea_synth = IdeaSynthesizer()
            st.header("Code Generator")
            st.write("Generate high-quality, documented Python code from a simple prompt.")

            with st.form("function_generator_form"):
                st.subheader("Generate a Function")
                function_prompt = st.text_input("Describe the function you want to create:", "a function that calculates the factorial of a number")
                submitted_function = st.form_submit_button("Generate Function")

                if submitted_function:
                    if not function_prompt:
                        st.warning("Please enter a description.")
                    else:
                        with st.spinner("The Giblet is generating your function..."):
                            try:
                                response = httpx.post("http://localhost:8000/generate/function", json={"prompt": function_prompt}, timeout=60)
                                response.raise_for_status()
                                generated_code = response.json().get("generated_code", "# An error occurred.")
                                st.code(generated_code, language="python")
                            except httpx.RequestError as e_api:
                                st.error(f"API Request Failed. Is the Giblet API server running? Details: {sanitize_for_display(str(e_api))}")
                            except Exception as e_gen:
                                st.error(f"Error generating function: {sanitize_for_display(str(e_gen))}")

            st.divider()

            with st.form("test_generator_form"):
                st.subheader("Generate Unit Tests")
                test_file_path = st.text_input("Enter the path to the Python file to test:", "refactor_test.py")
                submitted_tests = st.form_submit_button("Generate Tests")

                if submitted_tests:
                    if not test_file_path:
                        st.warning("Please enter a file path.")
                    else:
                        with st.spinner("The Giblet is writing your tests..."):
                             try:
                                response = httpx.post("http://localhost:8000/generate/tests", json={"filepath": test_file_path}, timeout=60)
                                response.raise_for_status()
                                generated_code = response.json().get("generated_code", "# An error occurred.")
                                st.code(generated_code, language="python")
                             except httpx.RequestError as e_api:
                                st.error(f"API Request Failed. Is the Giblet API server running? Details: {sanitize_for_display(str(e_api))}")
                             except Exception as e_gen:
                                st.error(f"Error generating tests: {sanitize_for_display(str(e_gen))}")
        except Exception as e:
            st.error(f"Failed to initialize AI code generators: {sanitize_for_display(str(e))}")

    # <<< NEW: Refactor Cockpit Tab
    with tabs[3]:
        st.header("Code Refactor")
        st.write("Improve existing code by providing a file and a refactoring instruction.")

        with st.form("refactor_form"):
            refactor_filepath = st.text_input("Enter the path to the Python file to refactor:", "refactor_test.py")
            refactor_instruction = st.text_input("How should The Giblet refactor it?", "Add type hints to the function")

            submitted_refactor = st.form_submit_button("Analyze & Suggest Refactoring")

            if submitted_refactor:
                if not refactor_filepath or not refactor_instruction:
                    st.warning("Please provide both a file path and an instruction.")
                else:
                    with st.spinner("The Giblet is analyzing your code..."):
                        try:
                            response = httpx.post("http://localhost:8000/refactor", json={"filepath": refactor_filepath, "instruction": refactor_instruction}, timeout=60)
                            response.raise_for_status()
                            data = response.json()

                            # Store the result in Streamlit's session state to use later
                            st.session_state.original_code = data.get("original_code")
                            st.session_state.refactored_code = data.get("refactored_code")
                            st.session_state.refactor_filepath = refactor_filepath

                        except httpx.RequestError as e:
                            st.error(f"API Request Failed. Is the Giblet API server running? Details: {sanitize_for_display(str(e))}")
                        except Exception as e_refactor:
                            st.error(f"Error during refactoring: {sanitize_for_display(str(e_refactor))}")

        # Display the diff and the confirm button if a refactoring has been generated
        if 'refactored_code' in st.session_state and st.session_state.refactored_code:
            st.subheader("Proposed Changes")

            original = st.session_state.original_code.splitlines()
            refactored = st.session_state.refactored_code.splitlines()

            # Generate a visual diff
            diff = difflib.unified_diff(original, refactored, fromfile='Original', tofile='Refactored', lineterm='')
            diff_text = "\n".join(list(diff))

            st.code(diff_text, language='diff')

            if st.button("Confirm & Overwrite File"):
                with st.spinner("Saving changes..."):
                    # This part will call the /file/write endpoint
                    # Ensure your API and utils.write_file can handle the request
                    # For simplicity, directly using the refactored_code from session_state
                    write_response = httpx.post("http://localhost:8000/file/write", json={"filepath": st.session_state.refactor_filepath, "content": st.session_state.refactored_code}, timeout=10)
                    if write_response.status_code == 200:
                        st.success(f"✅ File '{st.session_state.refactor_filepath}' updated successfully!")
                        # Clear the state after saving
                        del st.session_state.refactored_code
                        del st.session_state.original_code
                        del st.session_state.refactor_filepath
                    else:
                        st.error(f"API Request Failed. Could not save the file. Server said: {write_response.text}")

    # <<< NEW: File Explorer Cockpit Tab
    with tabs[4]:
        st.header("Project File Explorer")

        try:
            # Get the list of all files from the API
            response = httpx.get("http://localhost:8000/files/list", timeout=10)
            response.raise_for_status()
            files = response.json().get("files", [])

            if not files:
                st.warning("No files found in the project.")
            else:
                # Add a blank option to the top of the list
                files.insert(0, "")
                selected_file = st.selectbox("Select a file to view its contents:", files)

                if selected_file:
                    # If a file is selected, fetch and display its content
                    with st.spinner(f"Reading {selected_file}..."):
                        read_response = httpx.get(f"http://localhost:8000/file/read?filepath={selected_file}", timeout=10)
                        read_response.raise_for_status()
                        file_data = read_response.json()

                        st.subheader(f"Contents of `{file_data.get('filepath')}`")
                        # Determine language for syntax highlighting based on file extension
                        lang = file_data.get('filepath', '').split('.')[-1]
                        if lang == 'py': lang = 'python'
                        if lang == 'md': lang = 'markdown'

                        st.code(file_data.get("content", "Could not load content."), language=lang)

        except httpx.RequestError as e:
            st.error(f"API Request Failed. Is the Giblet API server running? Details: {sanitize_for_display(str(e))}")

    # <<< NEW: Automation Cockpit Tab
    with tabs[5]:
        st.header("Project Automation")

        st.subheader("Generate Changelog")
        if st.button("Generate from Git History", use_container_width=True, key="btn_changelog"):
            with st.spinner("Analyzing Git history..."):
                try:
                    response = httpx.post("http://localhost:8000/automate/changelog", timeout=30)
                    response.raise_for_status()
                    result = response.json()
                    if "error" in result:
                        st.error(f"Changelog generation failed: {result['error']}")
                    else:
                        st.success(result["message"])
                except httpx.RequestError as e_api:
                    st.error(f"API Request Failed. Is the Giblet API server running? Details: {sanitize_for_display(str(e_api))}")
                except Exception as e_cl:
                    st.error(f"Error generating changelog: {sanitize_for_display(str(e_cl))}")

        st.divider()

        st.subheader("Add TODO Stubs")
        stub_filepath = st.text_input("Enter the path to a Python file:", "test_file.py", key="txt_stub_file")
        if st.button("Add Stubs", use_container_width=True, key="btn_stubs"):
            if not stub_filepath:
                st.warning("Please enter a file path.")
            else:
                with st.spinner(f"Analyzing {stub_filepath}..."):
                    try:
                        response = httpx.post("http://localhost:8000/automate/stubs", json={"filepath": stub_filepath}, timeout=30)
                        response.raise_for_status()
                        result = response.json()
                        if "error" in result:
                            st.error(f"Stub generation failed for {stub_filepath}: {result['error']}")
                        else:
                            st.success(result["message"])
                    except httpx.RequestError as e_api:
                        st.error(f"API Request Failed. Is the Giblet API server running? Details: {sanitize_for_display(str(e_api))}")
                    except Exception as e_stub:
                        st.error(f"Error generating stubs for {stub_filepath}: {sanitize_for_display(str(e_stub))}")
if __name__ == "__main__":
    main()