# dashboard.py
import streamlit as st
import httpx
import sys
from pathlib import Path

# This line ensures that the script can find your 'core' modules
sys.path.append(str(Path(__file__).parent))

from core.roadmap_manager import RoadmapManager
from core.git_analyzer import GitAnalyzer
from core.idea_synth import IdeaSynthesizer
from core.memory import Memory

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

    # --- Create a tabbed interface ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Roadmap", "📜 History", "🛠️ Generator"])

    with tab1:
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
                    with st.expander(f"**{phase_name}**", expanded=True):
                        for task in phase_tasks:
                            is_complete = (task['status'] == 'complete')
                            st.checkbox(task['description'], value=is_complete, disabled=True)

        except httpx.RequestError:
            st.error("Could not connect to The Giblet API. Is the server running?")

    with tab2:
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
                        st.markdown(f"**Commit:** `{commit['sha']}`")
                        st.text(f"Author: {commit['author']} | Date: {commit['date']}")
                        st.info(f"{commit['message']}", icon="💬")
                        st.divider()
        except Exception as e:
            st.error(f"Could not load Git history: {e}")


    with tab3:
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
                            except httpx.RequestError as e:
                                st.error(f"API Request Failed. Is the Giblet API server running?")

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
                             except httpx.RequestError as e:
                                st.error(f"API Request Failed. Is the Giblet API server running?")
        except Exception as e:
            st.error(f"Failed to initialize AI code generators: {e}")

if __name__ == "__main__":
    main()