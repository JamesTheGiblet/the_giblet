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
    # For Genesis Mode
    if 'genesis_conversation' not in st.session_state:
        st.session_state.genesis_conversation = []
    if 'genesis_session_active' not in st.session_state:
        st.session_state.genesis_session_active = False
    if 'genesis_final_brief' not in st.session_state:
        st.session_state.genesis_final_brief = None
    if 'generated_readme' not in st.session_state: # For README generation
        st.session_state.generated_readme = None

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
        st.header("🧬 Project Genesis Mode - Idea Interview")
        st.write("""
            Start a new project from scratch! Provide an initial idea, and The Giblet's
            Idea Interpreter will engage in a Q&A to refine it into a detailed project brief.
        """)

        # Display conversation history
        for message in st.session_state.genesis_conversation:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if not st.session_state.genesis_session_active and not st.session_state.genesis_final_brief:
            initial_idea_input = st.text_area("Enter your initial project idea to begin:", height=100, key="genesis_initial_idea_input",
                                        help="e.g., 'A mobile app to identify plants using the phone camera.'")
            if st.button("🚀 Start Interpretation", key="start_genesis_interpretation_btn"):
                if initial_idea_input.strip():
                    with st.spinner("Interpreter is preparing questions..."):
                        # This would now be an API call
                        try:
                            response = httpx.post("http://localhost:8000/genesis/start", json={"initial_idea": initial_idea_input}, timeout=60)
                            response.raise_for_status()
                            data = response.json()
                            if data.get("error"):
                                st.error(f"Failed to start interpretation: {data['error']}")
                            else:
                                questions = data.get("questions")
                                st.session_state.genesis_conversation.append({"role": "user", "content": f"My idea: {initial_idea_input}"})
                                st.session_state.genesis_conversation.append({"role": "assistant", "content": questions})
                                st.session_state.genesis_session_active = True
                                st.rerun()
                        except Exception as e:
                            st.error(f"API Request Failed (Genesis Start): {e}")
                else:
                    st.warning("Please enter an initial idea.")

        if st.session_state.genesis_session_active:
            user_answer = st.chat_input("Your answer:", key="genesis_user_answer")
            if user_answer:
                st.session_state.genesis_conversation.append({"role": "user", "content": user_answer})
                with st.spinner("Interpreter is processing your answer..."):
                    try:
                        # This would now be an API call
                        response = httpx.post("http://localhost:8000/genesis/answer", json={"answer": user_answer}, timeout=120)
                        response.raise_for_status()
                        data = response.json()

                        if data.get("status") == "complete":
                            st.session_state.genesis_conversation.append({"role": "assistant", "content": "Great! I've synthesized a project brief based on our conversation."})
                            st.session_state.genesis_final_brief = data.get("data")
                            st.session_state.genesis_session_active = False
                        elif data.get("status") == "in_progress":
                            st.session_state.genesis_conversation.append({"role": "assistant", "content": data.get("data")})
                        elif data.get("status") == "error":
                            st.error(f"An error occurred: {data.get('message', 'Unknown error')}")
                            st.session_state.genesis_session_active = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"API Request Failed (Genesis Answer): {e}")
                        st.session_state.genesis_session_active = False # End session on error
                        st.rerun()


        if st.session_state.genesis_final_brief:
            st.subheader("📝 Final Project Brief")
            st.json(st.session_state.genesis_final_brief)

            # --- NEW README GENERATION UI ---
            if 'generated_readme' not in st.session_state:
                st.session_state.generated_readme = None

            if st.button("Generate Project README", key="generate_project_readme_btn"):
                with st.spinner("Generating style-aware README..."):
                    try:
                        payload = {"project_brief": st.session_state.genesis_final_brief}
                        response = httpx.post("http://localhost:8000/generate/readme", json=payload, timeout=120)
                        response.raise_for_status()
                        st.session_state.generated_readme = response.json().get("readme_content")
                    except Exception as e:
                        st.error(f"Failed to generate README: {e}")

            if st.session_state.generated_readme:
                with st.expander("Generated README.md", expanded=True):
                    st.markdown(st.session_state.generated_readme)
                    # Add a button to save the README to a file
                    if st.button("Save README.md to disk", key="save_readme_disk_btn"):
                         with st.spinner("Saving..."):
                            try:
                                write_payload = {"filepath": "README.md", "content": st.session_state.generated_readme}
                                write_response = httpx.post("http://localhost:8000/file/write", json=write_payload, timeout=10)
                                write_response.raise_for_status()
                                st.success("✅ README.md saved successfully!")
                            except Exception as e:
                                st.error(f"Failed to save README.md: {e}")
            # --- END NEW UI ---

            if st.button("Start New Genesis Session", key="restart_genesis_btn"):
                st.session_state.genesis_conversation = []
                st.session_state.genesis_session_active = False
                st.session_state.genesis_final_brief = None
                st.session_state.generated_readme = None # Clear readme on restart
                st.rerun()

    elif st.session_state.active_tab == "🗺️ Roadmap":
        st.header("🗺️ Project Roadmap")
        try:
            response = httpx.get("http://localhost:8000/roadmap", timeout=10)
            response.raise_for_status()
            data = response.json()
            tasks = data.get("roadmap", [])

            if not tasks:
                st.warning("No tasks found in roadmap.md")
            else:
                phases = {}
                current_phase = "General Tasks"
                for task in tasks:
                    if 'Phase' in task['description'] or task['description'].lower().startswith("phase "):
                        current_phase = task['description']
                        if current_phase not in phases:
                            phases[current_phase] = []
                    else:
                        if current_phase not in phases: # Should be initialized
                            phases[current_phase] = []
                        phases[current_phase].append(task)

                for phase_name, phase_tasks in phases.items():
                    with st.expander(f"**{phase_name}**", expanded=True):
                        for task_item in phase_tasks:
                            is_complete = (task_item['status'] == 'complete')
                            st.checkbox(task_item['description'], value=is_complete, disabled=True, key=f"task_{phase_name}_{task_item['description'][:20]}")
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
        except Exception as e: # Catch other potential errors like JSONDecodeError
            st.error(f"An unexpected error occurred in File Explorer: {e}")

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