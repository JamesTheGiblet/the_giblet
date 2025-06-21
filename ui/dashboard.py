# dashboard.py
import httpx
import streamlit as st
import sys
from pathlib import Path

# This line ensures that the script can find your 'core' modules
import difflib
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ui.dashboard_api_client import GibletAPIClient
from ui.dashboard_utils import format_code_diff
from ui.session_state_manager import initialize_session_state
from ui.dashboard_components import render_sidebar_navigation


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
    initialize_session_state()
    
    api_client = GibletAPIClient()


    with st.sidebar:
        render_sidebar_navigation()

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
            # --- Input area for user's idea OR random idea generation ---
            col1, col2 = st.columns([3, 1])

            with col1:
                initial_idea_input = st.text_area("Enter your initial project idea to begin:", height=100, key="genesis_initial_idea_input",
                                                help="e.g., 'A mobile app to identify plants using the phone camera.'")

            with col2:
                st.write("") 
                st.write("") 
                if st.button("🎲 Surprise Me!", use_container_width=True, help="Generate a random, weird project idea to start with.", key="surprise_me_btn"):
                    with st.spinner("Summoning a strange idea..."):
                        try: # Use the API client
                            response_random_idea = api_client.get_random_weird_idea()
                            response_random_idea.raise_for_status()
                            data_random_idea = response_random_idea.json()
                            random_idea = data_random_idea.get("idea")
                            
                            if random_idea:
                                response_genesis_start = httpx.post("http://localhost:8000/genesis/start", json={"initial_idea": random_idea}, timeout=60)
                                response_genesis_start.raise_for_status()
                                data_genesis_start = api_client.genesis_start(random_idea)

                                if data_genesis_start.get("error"):
                                    st.error(f"Failed to start interpretation with random idea: {data_genesis_start['error']}")
                                else:
                                    questions = data_genesis_start.get("questions")
                                    st.session_state.genesis_conversation = [] 
                                    st.session_state.genesis_final_brief = None
                                    st.session_state.genesis_conversation.append({"role": "user", "content": f"My random idea: {random_idea}"})
                                    st.session_state.genesis_conversation.append({"role": "assistant", "content": questions})
                                    st.session_state.genesis_session_active = True
                                    st.rerun()
                            else:
                                st.error("The API did not return a random idea.")

                        except Exception as e:
                            st.error(f"Failed to get or process a random idea: {e}")

            # Button to start interpretation with manually entered idea
            if st.button("🚀 Start Interpretation", key="start_genesis_interpretation_btn"):
                if initial_idea_input.strip():
                    with st.spinner("Interpreter is preparing questions..."):
                        try: # Use the API client
                            response = api_client.genesis_start(initial_idea_input)
                            response.raise_for_status()
                            data = response.json()
                            if data.get("error"):
                                st.error(f"Failed to start interpretation: {data['error']}")
                            else:
                                questions_manual = data.get("questions")
                                st.session_state.genesis_conversation = [] 
                                st.session_state.genesis_final_brief = None
                                st.session_state.genesis_conversation.append({"role": "user", "content": f"My idea: {initial_idea_input}"})
                                st.session_state.genesis_conversation.append({"role": "assistant", "content": questions_manual})
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
                    try: # Use the API client
                        response = api_client.genesis_answer(user_answer)
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
                        st.session_state.genesis_session_active = False 
                        st.rerun()


        if st.session_state.genesis_final_brief:
            st.subheader("📝 Final Project Brief")
            st.json(st.session_state.genesis_final_brief)

            col1, col2 = st.columns(2)

            with col1:
                if 'generated_readme' not in st.session_state:
                    st.session_state.generated_readme = None

                if st.button("Generate Project README", key="generate_project_readme_btn", use_container_width=True):
                    with st.spinner("Generating style-aware README..."):
                        try:
                            response = api_client.generate_readme(st.session_state.genesis_final_brief)
                            response.raise_for_status()
                            st.session_state.generated_readme = response.json().get("readme_content")
                        except Exception as e:
                            st.error(f"Failed to generate README: {e}")

            with col2:
                if 'generated_roadmap' not in st.session_state:
                    st.session_state.generated_roadmap = None
                
                if st.button("Generate Project Roadmap", key="generate_project_roadmap_btn", use_container_width=True):
                    with st.spinner("Generating style-aware roadmap..."):
                        try: # Use the API client
                            response = api_client.generate_roadmap(st.session_state.genesis_final_brief)
                            response.raise_for_status()
                            st.session_state.generated_roadmap = response.json().get("roadmap_content")
                        except Exception as e:
                            st.error(f"Failed to generate roadmap: {e}")

            if st.session_state.generated_readme:
                with st.expander("Generated README.md", expanded=True):
                    st.markdown(st.session_state.generated_readme)
                    if st.button("Save README.md to disk", key="save_readme_disk_btn"):
                            with st.spinner("Saving..."): # Use the API client
                                try:
                                    write_response = api_client.write_file("README.md", st.session_state.generated_readme)
                                    write_response.raise_for_status()
                                    st.success("✅ README.md saved successfully!", icon="📄")
                                except Exception as e:
                                    st.error(f"Failed to save README.md: {e}")

                    st.info("Did you like this format? You can make it your default.")
                    if st.button("Save README Style as Default", key="save_readme_style_btn"):
                        if st.session_state.get('last_readme_settings'):
                            with st.spinner("Saving default style..."):
                                try: # Use the API client
                                    response = api_client.set_style_preferences(
                                        "readme", st.session_state.last_readme_settings
                                    )
                                    response.raise_for_status()
                                    st.toast("✅ README style preferences updated!")
                                except Exception as e:
                                    st.error(f"Failed to save style: {e}")
                        else:
                            st.warning("Could not find the style settings for the last README.")
            
            if st.session_state.generated_roadmap:
                with st.expander("Generated roadmap.md", expanded=True):
                    st.markdown(st.session_state.generated_roadmap)
                    if st.button("Save roadmap.md to disk", key="save_roadmap_disk_btn"):
                            with st.spinner("Saving..."): # Use the API client
                                try:
                                    write_response = api_client.write_file("roadmap.md", st.session_state.generated_roadmap)
                                    write_response.raise_for_status()
                                    st.success("✅ roadmap.md saved successfully!", icon="🗺️")
                                except Exception as e:
                                    st.error(f"Failed to save roadmap.md: {e}")

            if st.session_state.get('generated_readme') and st.session_state.get('generated_roadmap'):
                st.divider()
                st.header("🚀 Build Workspace")
                st.write("Your project is fully planned. Choose how you want to create the workspace.")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Create Local Project Folder", use_container_width=True):
                        with st.spinner("Scaffolding local project..."):
                            try: # Use the API client
                                response = api_client.scaffold_local_project(
                                    st.session_state.genesis_final_brief.get("title", "new_giblet_project"), st.session_state.genesis_final_brief
                                )
                                response.raise_for_status()
                                data = response.json()
                                st.success(data.get("message"))
                                st.info(f"Project created at: {data.get('path')}")
                            except Exception as e:
                                st.error(f"Failed to create local project: {e}")

                with col2:
                    if st.button("Create Private GitHub Repo", use_container_width=True):
                        st.info("Ensure your `GITHUB_TOKEN` is set as an environment variable for the API server.", icon="🔑")
                        with st.spinner("Creating GitHub repository..."): # Use the API client
                            try:
                                response = api_client.create_github_repo(
                                    st.session_state.genesis_final_brief.get("title", "new-giblet_project").lower().replace(" ", "-"),
                                    st.session_state.genesis_final_brief.get("summary", "A new project generated by The Giblet."),
                                    True
                                )
                                response.raise_for_status()
                                data = response.json()
                                st.success(data.get("message"))
                                st.markdown(f"**Repo URL:** {data.get('url')})")
                            except Exception as e:
                                st.error(f"Failed to create GitHub repo: {e}")

            if st.button("Start New Genesis Session", key="restart_genesis_btn"):
                st.session_state.genesis_conversation = []
                st.session_state.genesis_session_active = False
                st.session_state.genesis_final_brief = None
                st.session_state.generated_readme = None
                st.session_state.generated_roadmap = None
                st.rerun()

    elif st.session_state.active_tab == "🗺️ Roadmap":
        st.header("🗺️ Project Roadmap")
        try: # Increased timeout for robustness, as API server might be slow to initialize LLM components
            response = api_client.get_roadmap()
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
                        if current_phase not in phases:
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
            st.session_state.agent_plan = None
            st.session_state.agent_execution_result = None
            if not goal.strip():
                st.warning("Please enter a goal.")
            else:
                with st.spinner("Agent is thinking and creating a plan..."):
                    try: # Use the API client
                        response = api_client.agent_plan(goal)
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
                st.session_state.agent_execution_result = None
                with st.spinner("Agent is executing the plan... This may take a while. Check API console for detailed logs."): # Use the API client
                    try:
                        response = api_client.agent_execute()
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
        st.header("📂 Universal File Explorer")

        # Source selection
        source_type = st.radio(
            "Select file source:",
            ["Local Filesystem", "GitHub Repository"],
            key="explorer_source_radio",
            horizontal=True,
            on_change=lambda: st.session_state.update(explorer_files=[], explorer_selected_file_path=None, explorer_selected_file_content=None) # Reset on change
        )
        st.session_state.explorer_source = source_type

        # --- GitHub Source UI ---
        if st.session_state.explorer_source == "GitHub Repository":
            st.info("Ensure your `GITHUB_TOKEN` is set as an environment variable for the API server.", icon="🔑")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.session_state.explorer_github_owner = st.text_input("GitHub Owner", value=st.session_state.explorer_github_owner, key="github_owner_input")
            with col2:
                st.session_state.explorer_github_repo = st.text_input("GitHub Repo Name", value=st.session_state.explorer_github_repo, key="github_repo_input")
            with col3:
                st.write("") # Spacer
                if st.button("Fetch Repo Files", use_container_width=True, key="fetch_github_files_btn"):
                    if st.session_state.explorer_github_owner and st.session_state.explorer_github_repo: # Use the API client
                        with st.spinner("Fetching file list from GitHub..."):
                            try:
                                response = api_client.list_github_repo_contents(st.session_state.explorer_github_owner, st.session_state.explorer_github_repo)
                                response.raise_for_status()
                                st.session_state.explorer_files = response.json().get("files", [])
                            except Exception as e:
                                st.error(f"Failed to fetch GitHub repo contents: {e}")
                                st.session_state.explorer_files = []
                    else:
                        st.warning("Please provide both GitHub owner and repo name.")

        # --- Local Filesystem Source ---
        else: # Local
            if st.button("Refresh Local Files", key="refresh_local_files_btn"):
                with st.spinner("Scanning local files..."): # Use the API client
                    try:
                        response = api_client.list_local_files()
                        response.raise_for_status()
                        st.session_state.explorer_files = response.json().get("files", [])
                    except Exception as e:
                        st.error(f"Could not load file list: {e}")
                        st.session_state.explorer_files = []
            # Initial load for local files
            if not st.session_state.explorer_files:
                try: # Use the API client
                    response = api_client.list_local_files()
                    response.raise_for_status()
                    st.session_state.explorer_files = response.json().get("files", [])
                except Exception: # Silently fail on initial load if API is not ready
                    pass

        # --- File Selection and Display (Common Logic) ---
        if st.session_state.explorer_files:
            selected_file = st.selectbox(
                "Select a file to view:",
                [""] + st.session_state.explorer_files,
                key="explorer_file_selector"
            )

            if selected_file and selected_file != st.session_state.get('explorer_selected_file_path'):
                st.session_state.explorer_selected_file_path = selected_file
                with st.spinner(f"Reading {selected_file}..."):
                    try: # Use the API client
                        if st.session_state.explorer_source == "GitHub Repository":
                            read_response = api_client.get_github_file_content(st.session_state.explorer_github_owner, st.session_state.explorer_github_repo, selected_file)
                        else: # Local
                            read_response = api_client.read_file(selected_file)
                        
                        read_response.raise_for_status()
                        file_data = read_response.json()
                        st.session_state.explorer_selected_file_content = file_data.get("content", "# Error: Could not load content.")
                    except Exception as e:
                        st.error(f"Error reading file '{selected_file}': {e}")
                        st.session_state.explorer_selected_file_content = f"# Error reading file:\n\n{e}"
        else:
            st.info("No files to display. Fetch files from a source above.")

        if st.session_state.get('explorer_selected_file_content'):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"Source: `{st.session_state.explorer_selected_file_path}`")
                lang = st.session_state.explorer_selected_file_path.split('.')[-1]
                st.code(st.session_state.explorer_selected_file_content, language=lang if lang != 'md' else 'markdown', line_numbers=True)
            with col2:
                st.subheader("Living Documentation")
                readme_path = f"{st.session_state.explorer_selected_file_path}.readme.md"
                # This part only works for local files currently.
                # A more advanced implementation would check for .readme.md files in GitHub too.
                if st.session_state.explorer_source == "Local Filesystem" and readme_path in st.session_state.explorer_files: # Use the API client
                    with st.spinner(f"Loading documentation..."):
                        readme_resp = api_client.read_file(readme_path)
                        if readme_resp.status_code == 200:
                            st.markdown(readme_resp.json().get("content", "*Could not load documentation.*"))
                        else:
                            st.warning("Documentation file found but could not be read.")
                else:
                    st.info("No Living Documentation found for this file.")

    elif st.session_state.active_tab == "🤖 Automation":
        st.header("Project Automation")

        st.subheader("Generate Changelog")
        if st.button("Generate from Git History", key="btn_changelog"):
            with st.spinner("Analyzing Git history..."): # Use the API client
                try:
                    response = api_client.generate_changelog()
                    response.raise_for_status()
                    st.success(response.json().get("message", "Changelog generated!"))
                except Exception as e:
                    st.error(f"Failed to generate changelog: {e}")

        st.divider()

        st.subheader("Add TODO Stubs")
        stub_filepath = st.text_input("Enter the path to a Python file:", "core/agent.py", key="txt_stub_file")
        if st.button("Add Stubs", key="btn_stubs"):
            if stub_filepath: # Use the API client
                with st.spinner(f"Analyzing {stub_filepath}..."):
                    try:
                        response = api_client.add_stubs(stub_filepath)
                        response.raise_for_status()
                        st.success(response.json().get("message", "Stubs added!"))
                    except Exception as e:
                        st.error(f"Failed to add stubs: {e}")
            else:
                st.warning("Please enter a file path.")
    
    # New Tab for Code Analysis
    elif st.session_state.active_tab == "🔬 Code Analysis":
        st.header("🔬 Code Duplication Analysis")
        st.write("Scan the project codebase for structurally and conceptually similar functions.")
        
        if st.button("⚡ Scan for Duplicates", use_container_width=True, type="primary"):
            st.session_state.duplication_report = None # Clear previous report # Use the API client
            with st.spinner("Analyzing codebase... This may take a moment."):
                try:
                    response = api_client.analyze_duplicates()
                    response.raise_for_status()
                    st.session_state.duplication_report = response.json()
                except Exception as e:
                    st.error(f"Failed to run duplication analysis: {e}")
                    st.session_state.duplication_report = {"error": str(e)}
    
    elif st.session_state.active_tab == "✨ Refactor":
        st.header("✨ Code Refactor & Diff")
        st.write("Enter Python code and a refactoring instruction. The Giblet will suggest a refactored version and show the differences.")

        col_input, col_output = st.columns(2)

        with col_input:
            st.subheader("Original Code")
            refactor_code_input = st.text_area("Enter Python code to refactor:", height=400, key="refactor_code_input")
            refactor_instruction = st.text_input("Refactoring Instruction:", key="refactor_instruction")

            if st.button("Refactor Code", key="refactor_btn", use_container_width=True):
                if not refactor_code_input.strip():
                    st.warning("Please enter Python code to refactor.")
                    st.stop()
                if not refactor_instruction.strip():
                    st.warning("Please provide a refactoring instruction.")
                    st.stop()

                with st.spinner("Refactoring code..."): # Use the API client
                    try:
                        response = api_client.refactor_code(refactor_code_input, refactor_instruction)
                        response.raise_for_status()
                        data = response.json()
                        st.session_state.original_code_refactor = data.get("original_code")
                        st.session_state.refactored_code_refactor = data.get("refactored_code")
                        st.session_state.refactor_explanation = data.get("explanation")
                        st.success("Refactoring complete!")
                    except Exception as e:
                        st.error(f"Error during refactoring: {e}")

        with col_output:
            st.subheader("Refactored Code & Diff")
            if st.session_state.get("refactored_code_refactor"):
                # Display the explanation in an expander
                if st.session_state.get("refactor_explanation"):
                    with st.expander("✨ Refactoring Explanation", expanded=True):
                        st.markdown(st.session_state.refactor_explanation)

                st.code(st.session_state.refactored_code_refactor, language="python")

                st.markdown("---")
                st.subheader("Code Differences")
                original_lines = st.session_state.original_code_refactor.splitlines(keepends=True)
                refactored_lines = st.session_state.refactored_code_refactor.splitlines(keepends=True)
                
                diff = difflib.unified_diff(
                    original_lines,
                    refactored_lines,
                    fromfile="original.py",
                    tofile="refactored.py",
                    lineterm="" # Avoid extra newlines
                )
                st.code("".join(diff), language="diff")
            else:
                st.info("Refactored code and explanation will appear here after generation.")

        if st.session_state.duplication_report:
            report = st.session_state.duplication_report
            if "error" in report:
                # Error already displayed during the API call
                pass
            else:
                st.divider()
                # --- Display Syntactic Duplicates ---
                syntactic_dupes = report.get('syntactic', [])
                if not syntactic_dupes:
                    st.success("✅ No structurally duplicate functions found.")
                else:
                    st.subheader(f"🚨 Found {len(syntactic_dupes)} Group(s) of Structural Duplicates")
                    for i, group in enumerate(syntactic_dupes, 1):
                        with st.expander(f"Structural Group {i} ({len(group)} locations)", expanded=True):
                            for loc in group:
                                st.code(f"File: {loc['file']}\nFunction: {loc['function_name']}\nLine: {loc['line_number']}", language="text")
                
                st.divider()
                # --- Display Semantic Duplicates ---
                semantic_dupes = report.get('semantic', [])
                if not semantic_dupes:
                    st.success("✅ No conceptually similar functions found.")
                else:
                    st.subheader(f"🚨 Found {len(semantic_dupes)} Group(s) of Conceptual Duplicates")
                    for i, group in enumerate(semantic_dupes, 1):
                        with st.expander(f"Conceptual Group {i} ({len(group)} locations)", expanded=True):
                            for loc in group:
                                st.markdown(f"**File:** `{loc['file']}` | **Function:** `{loc['function_name']}` (Line: {loc['line_number']})")
                                st.info(f"**Docstring:** \"{loc['docstring']}\"")
                                st.write("---")


if __name__ == "__main__":
    main()
