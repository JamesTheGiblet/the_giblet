# dashboard.py
import streamlit as st
import httpx
import sys
from pathlib import Path
import json # Add this
import shlex # For parsing plan steps
import subprocess # For launching the gauntlet editor
import difflib

# This line ensures that the script can find your 'core' modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.memory import Memory
from core.user_profile import UserProfile
from core.llm_provider_base import LLMProvider # Import base provider
from core.llm_providers import GeminiProvider, OllamaProvider # Import specific providers
from core.style_preference import StylePreferenceManager
from core.project_contextualizer import ProjectContextualizer # Import ProjectContextualizer
from core.idea_interpreter import IdeaInterpreter # Import IdeaInterpreter
# Note: Other direct core imports are removed as logic is now handled via API calls


def main():
    """
    The main function for the Streamlit dashboard.
    """
    st.set_page_config(
        page_title="The Giblet Dashboard",
        page_icon="🧠",
        layout="wide"
    )

    # --- Session State Initialization ---
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "🧬 Genesis Mode"
    if 'agent_plan' not in st.session_state:
        st.session_state.agent_plan = None
    if 'agent_execution_result' not in st.session_state:
        st.session_state.agent_execution_result = None
    # Add other session state initializations as needed...

    # --- Sidebar ---
    with st.sidebar:
        st.header("🚀 Quick Actions")
        tab_names = ["🧬 Genesis Mode", "🗺️ Roadmap", "🛠️ Agent & Generator", "✨ Refactor", "📂 File Explorer", "🤖 Automation", "👤 Profile", "🎨 My Vibe"]

        for tab_name in tab_names:
            if st.button(tab_name, key=f"sidebar_nav_{tab_name.replace(' ', '_')}", use_container_width=True):
                st.session_state.active_tab = tab_name
                st.rerun()

    st.title("🧠 The Giblet: Project Cockpit")

    # --- Tab Content ---
    if st.session_state.active_tab == "🧬 Genesis Mode":
        # This section remains largely the same as your excellent implementation
        st.header("🧬 Project Genesis Mode - Idea Interview")
        # (Your existing Genesis Mode UI code goes here)

    elif st.session_state.active_tab == "🗺️ Roadmap":
        st.header("🗺️ Project Roadmap")
        try:
            response = httpx.get("http://localhost:8000/roadmap", timeout=10)
            response.raise_for_status()
            # (Your existing roadmap display code goes here)
        except Exception as e:
            st.error(f"Could not load roadmap. Is the API server running? Error: {e}")

    elif st.session_state.active_tab == "🛠️ Agent & Generator":
        st.header("🛠️ Autonomous Agent & Code Generator")
        st.write("Define a high-level goal, let the agent create a plan, and then execute it.")

        goal = st.text_area("Enter your high-level goal:", height=100, key="agent_goal_input",
                            help="e.g., 'Create a Python function to calculate Fibonacci numbers, write tests for it, and then run the tests.'")

        if st.button("Generate Plan", key="agent_generate_plan_btn"):
            st.session_state.agent_plan = None # Clear previous plan
            st.session_state.agent_execution_result = None # Clear previous execution result
            if not goal.strip():
                st.warning("Please enter a goal.")
            else:
                with st.spinner("Agent is thinking and creating a plan..."):
                    try:
                        response = httpx.post("http://localhost:8000/agent/plan", json={"goal": goal}, timeout=60)
                        response.raise_for_status()
                        data = response.json()
                        if data.get("error"):
                            st.error(f"Failed to generate plan: {data['error']}")
                        else:
                            st.session_state.agent_plan = data.get("plan")
                            st.success("Plan generated successfully!")
                    except Exception as e:
                        st.error(f"API Request Failed (Plan Generation): {e}")

        if st.session_state.agent_plan:
            st.subheader("Generated Plan:")
            for i, step in enumerate(st.session_state.agent_plan, 1):
                st.code(f"Step {i}: {step}", language="bash")

            st.warning("Review the plan carefully before execution.")
            if st.button("🚀 Execute Plan", type="primary", key="agent_execute_plan_btn"):
                st.session_state.agent_execution_result = None # Clear previous result
                with st.spinner("Agent is executing the plan... This may take a while. Check API console for detailed logs."):
                    try:
                        # This endpoint now executes the plan stored in memory by the API
                        response = httpx.post("http://localhost:8000/agent/execute", timeout=300) # Increased timeout
                        response.raise_for_status()
                        st.session_state.agent_execution_result = response.json()
                    except Exception as e:
                        st.error(f"Error during plan execution: {e}")

        if st.session_state.agent_execution_result:
            st.subheader("Execution Result")
            res = st.session_state.agent_execution_result
            st.success(res.get('message', 'Execution finished.'))
            st.json({
                "Steps Executed": res.get('steps_executed'),
                "Initial Test Failures": res.get('tests_failed_initial'),
                "Self-Correction Fix Attempts": res.get('fix_attempts'),
                "Self-Correction Succeeded": res.get('self_correction_successful'),
            })
            if res.get("final_error"):
                st.error(f"Final Error: {res.get('final_error')}")

    elif st.session_state.active_tab == "📂 File Explorer":
        st.header("📂 Project File Explorer")
        try:
            response = httpx.get("http://localhost:8000/files/list", timeout=10)
            response.raise_for_status()
            files = response.json().get("files", [])
            selected_file = st.selectbox("Select a file to view:", [""] + files)

            if selected_file:
                col1, col2 = st.columns(2)

                # --- Source Code Column ---
                with col1:
                    st.subheader(f"Source: `{selected_file}`")
                    with st.spinner(f"Reading {selected_file}..."):
                        read_response = httpx.get(f"http://localhost:8000/file/read?filepath={selected_file}", timeout=10)
                        read_response.raise_for_status()
                        file_data = read_response.json()
                        lang = selected_file.split('.')[-1]
                        st.code(file_data.get("content", ""), language=lang if lang != 'md' else 'markdown')

                # --- Living Documentation Column ---
                with col2:
                    st.subheader("Living Documentation")
                    readme_path = f"{selected_file}.readme.md"
                    if readme_path in files:
                        with st.spinner(f"Loading documentation..."):
                            readme_resp = httpx.get(f"http://localhost:8000/file/read?filepath={readme_path}", timeout=10)
                            if readme_resp.status_code == 200:
                                st.markdown(readme_resp.json().get("content", "*Could not load documentation.*"))
                            else:
                                st.warning("Documentation file found but could not be read.")
                    else:
                        st.info("No Living Documentation found for this file. It will be generated automatically when the file is created or modified by the agent.")

        except httpx.RequestError as e:
            st.error(f"Could not load file explorer. Is the API running? Error: {e}")

    elif st.session_state.active_tab == "🤖 Automation":
        st.header("Project Automation")

        st.subheader("Generate Changelog")
        if st.button("Generate from Git History", key="btn_changelog"):
            with st.spinner("Analyzing Git history..."):
                try:
                    response = httpx.post("http://localhost:8000/automate/changelog", timeout=30)
                    response.raise_for_status()
                    st.success(response.json().get("message", "Changelog generated!"))
                except Exception as e:
                    st.error(f"Failed to generate changelog: {e}")

        st.divider()

        st.subheader("Add TODO Stubs")
        stub_filepath = st.text_input("Enter the path to a Python file:", "core/agent.py", key="txt_stub_file")
        if st.button("Add Stubs", key="btn_stubs"):
            if stub_filepath:
                with st.spinner(f"Analyzing {stub_filepath}..."):
                    try:
                        response = httpx.post("http://localhost:8000/automate/stubs", json={"filepath": stub_filepath}, timeout=30)
                        response.raise_for_status()
                        st.success(response.json().get("message", "Stubs added!"))
                    except Exception as e:
                        st.error(f"Failed to add stubs: {e}")
            else:
                st.warning("Please enter a file path.")

    # Add other tabs like "Refactor", "Profile", "My Vibe" here,
    # ensuring they use the correct API endpoints from api.py

if __name__ == "__main__":
    main()