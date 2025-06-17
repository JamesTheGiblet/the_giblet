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
from core.user_profile import UserProfile # Import UserProfile

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

    # Initialize Memory and UserProfile for dashboard-specific instantiations
    # Note: API calls will use their own instances initialized in api.py
    memory_instance = Memory()
    user_profile_instance = UserProfile(memory_system=memory_instance)

    st.title("🧠 The Giblet: Project Cockpit")

    # <<< UPDATED: Add a new tab for the refactor tool
    tabs = st.tabs(["🗺️ Roadmap", "📜 History", "🛠️ Generator", "✨ Refactor", "📂 File Explorer", "🤖 Automation", "👤 Profile"]) # New Profile tab

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
            # Pass the dashboard's user_profile and memory instances
            idea_synth = IdeaSynthesizer(user_profile=user_profile_instance, memory_system=memory_instance)
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

        st.divider() # Add a divider before Agent controls
        st.header("Autonomous Agent Control")
        st.write("Define a high-level goal, let the agent create a plan, and then execute it.")

        # Initialize session state variables if they don't exist
        if 'agent_plan' not in st.session_state:
            st.session_state.agent_plan = None
        if 'agent_execution_result' not in st.session_state:
            st.session_state.agent_execution_result = None

        goal = st.text_area("Enter your high-level goal:", height=100, key="agent_goal_input_in_generator",
                            help="e.g., 'Create a Python function to calculate Fibonacci numbers, write tests for it, and then run the tests.'")

        if st.button("Generate Plan", key="agent_generate_plan_btn_in_generator"):
            st.session_state.agent_plan = None # Clear previous plan
            st.session_state.agent_execution_result = None # Clear previous execution result
            if not goal.strip():
                st.warning("Please enter a goal.")
            else:
                with st.spinner("Agent is thinking and creating a plan..."):
                    try:
                        response = httpx.post("http://localhost:8000/agent/plan", json={"goal": goal}, timeout=120)
                        response.raise_for_status()
                        data = response.json()
                        if data.get("error"):
                            st.error(f"Failed to generate plan: {data.get('error')}")
                        elif data.get("plan"):
                            st.session_state.agent_plan = data.get("plan")
                            st.success("Plan generated successfully!")
                        else:
                            st.error("Received an unexpected response from the plan generation API.")
                    except httpx.RequestError as e_req:
                        st.error(f"API Request Failed (Plan Generation): {sanitize_for_display(str(e_req))}")
                    except Exception as e_gen:
                        st.error(f"Error during plan generation: {sanitize_for_display(str(e_gen))}")
        
        if st.session_state.agent_plan:
            st.subheader("Generated Plan:")
            for i, step in enumerate(st.session_state.agent_plan, 1):
                st.markdown(f"`Step {i}: giblet {step}`")
            
            st.warning("Review the plan carefully before execution. Execution will run commands on your system. Check API server console for detailed logs.")
            if st.button("Execute Plan", type="primary", key="agent_execute_plan_btn_in_generator"):
                st.session_state.agent_execution_result = None # Clear previous result
                with st.spinner("Agent is executing the plan... This may take a while. Check API console for detailed logs."):
                    try:
                        response = httpx.post("http://localhost:8000/agent/execute", timeout=600) 
                        response.raise_for_status()
                        st.session_state.agent_execution_result = response.json()
                        
                        if st.session_state.agent_execution_result:
                            res = st.session_state.agent_execution_result
                            st.markdown(f"**Execution Result:** {res.get('message')}")
                            if res.get("final_error"): st.error(f"Details: {res.get('final_error')}")
                            st.json({
                                "Steps Executed": res.get('steps_executed', 0),
                                "Initial Test Failures": res.get('tests_failed_initial', 0),
                                "Fix Attempts": res.get('fix_attempts', 0),
                                "Self-Correction Succeeded": res.get('self_correction_successful', 'N/A')
                            })
                    except httpx.TimeoutException: st.error("Agent execution timed out. The process might still be running. Check the API server console.")
                    except httpx.RequestError as e_req: st.error(f"API Request Failed (Plan Execution): {sanitize_for_display(str(e_req))}")
                    except Exception as e_exec: st.error(f"Error during plan execution: {sanitize_for_display(str(e_exec))}")
        elif st.session_state.agent_execution_result: # Display previous result if no current plan
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
    
    with tabs[6]: # Corresponds to "👤 Profile"
        st.header("User Profile Management")

        # Function to fetch profile data
        def fetch_profile():
            try:
                response = httpx.get("http://localhost:8000/profile", timeout=10)
                response.raise_for_status()
                data = response.json()
                st.session_state.user_profile_data = data.get("profile", {})
            except Exception as e:
                st.error(f"Failed to fetch profile: {sanitize_for_display(str(e))}")
                st.session_state.user_profile_data = {}

        # Initialize or refresh profile data
        if 'user_profile_data' not in st.session_state or st.button("Refresh Profile Data", key="refresh_profile_btn"):
            fetch_profile()

        st.subheader("Current Profile Settings")
        profile_data_to_display = st.session_state.get('user_profile_data')

        if profile_data_to_display is not None: # Check if it's initialized
            if not profile_data_to_display: # It's an empty dictionary
                st.info("User profile is currently empty. Use the 'Set a Preference' form below to add your settings.")
            else: # It has data
                for category, settings in profile_data_to_display.items():
                    if isinstance(settings, dict) and settings: # Check if settings is a non-empty dictionary
                        st.markdown(f"##### {category.replace('_', ' ').title()}")
                        for key, value in settings.items():
                            st.markdown(f"- **{key.replace('_', ' ').title()}:** `{value}`")
                        st.write("---") # Add a small divider between categories
                    elif settings: # If it's not a dict but has a value (less likely with current structure but good to handle)
                        st.markdown(f"- **{category.replace('_', ' ').title()}:** `{settings}`")

        st.divider()
        st.subheader("Set a Preference")
        with st.form("set_preference_form", clear_on_submit=True):
            # Predefined categories based on your DEFAULT_PROFILE_STRUCTURE
            # You might want to fetch these dynamically or define them more centrally
            # For now, let's hardcode based on your current default structure
            default_categories = ["general", "coding_style", "project_settings", "llm_settings", "ui_style"] # Added a few more common ones
            
            st.write("Select a category or type a new one:")
            pref_category_select = st.selectbox("Common Categories", options=default_categories, index=0, key="pref_cat_select", help="Choose a common category or type a custom one below.")
            pref_category_custom = st.text_input("Or Enter Custom Category", key="pref_cat_custom", help="If your category isn't listed, enter it here. This will override the selection above.")

            # Determine the category to use
            pref_category = pref_category_custom if pref_category_custom else pref_category_select
            
            pref_key = st.text_input(f"Preference Key for '{pref_category}' (e.g., 'user_name', 'indent_size')", key="pref_key", help="The specific name of the preference. For 'general', try 'user_name' or 'company_name'. For 'coding_style', try 'preferred_quote_type' or 'indent_size'.")
            pref_value = st.text_input("Preference Value", key="pref_val", help="The actual setting for this preference (e.g., 'James', 'Acme Corp', 'single', '2').")
            submitted_pref = st.form_submit_button("Set Preference")

            if submitted_pref:
                # Debug print
                st.write(f"DEBUG: Category='{pref_category}', Key='{pref_key}', Value='{pref_value}'")
                if pref_category and pref_key: # Value can be empty string
                    try:
                        payload = {"category": pref_category, "key": pref_key, "value": pref_value}
                        response = httpx.post("http://localhost:8000/profile/set", json=payload, timeout=10)
                        response.raise_for_status()
                        st.success(response.json().get("message", "Preference set!"))
                        fetch_profile() # Refresh data after setting
                    except Exception as e:
                        st.error(f"Failed to set preference: {sanitize_for_display(str(e))}")
                else:
                    st.warning("Category and Key are required to set a preference.")
        
        st.divider()
        st.subheader("Clear Profile")
        if st.button("Clear Entire User Profile", type="secondary", key="clear_profile_btn"):
            # Simple confirmation for now, could be a modal or more elaborate
            confirm_clear = st.checkbox("I understand this will delete all my profile settings.", key="confirm_clear_profile_cb")
            if confirm_clear:
                try:
                    response = httpx.post("http://localhost:8000/profile/clear", timeout=10)
                    response.raise_for_status()
                    st.success(response.json().get("message", "Profile cleared!"))
                    fetch_profile() # Refresh data after clearing
                except Exception as e:
                    st.error(f"Failed to clear profile: {sanitize_for_display(str(e))}")

        st.divider()
        st.subheader("Provide Feedback on Last AI Interaction")

        if 'last_interaction_for_feedback' not in st.session_state:
            st.session_state.last_interaction_for_feedback = None

        if st.button("Load Last Interaction for Feedback", key="load_last_interaction_btn"):
            try:
                response = httpx.get("http://localhost:8000/feedback/last_interaction", timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get("interaction"):
                    st.session_state.last_interaction_for_feedback = data.get("interaction") # This should be a dict
                else:
                    st.session_state.last_interaction_for_feedback = None
                    # Display the message from the API if no interaction is found
                    st.info(data.get("message", "No recent AI interaction available for feedback."))
            except Exception as e:
                st.error(f"Failed to load last interaction: {sanitize_for_display(str(e))}")
                st.session_state.last_interaction_for_feedback = None
        
        current_interaction = st.session_state.get('last_interaction_for_feedback')

        if current_interaction and isinstance(current_interaction, dict):
            interaction = current_interaction
            st.markdown(f"**Regarding:** `{interaction.get('module', 'N/A')}` - `{interaction.get('method', 'N/A')}`")
            st.markdown(f"**Prompt Summary:**")
            st.caption(f"`{interaction.get('prompt_summary', 'N/A')}`")
            st.markdown(f"**Output Summary:**")
            st.caption(f"`{interaction.get('output_summary', 'N/A')}`")

            with st.form("feedback_form", clear_on_submit=True):
                feedback_rating = st.radio("Your Rating:", ("positive", "neutral", "negative"), key="feedback_rating_radio", horizontal=True)
                feedback_comment = st.text_area("Optional Comment:", key="feedback_comment_area")
                submitted_feedback = st.form_submit_button("Submit Feedback")

                if submitted_feedback:
                    try:
                        payload = {"rating": feedback_rating, "comment": feedback_comment}
                        response = httpx.post("http://localhost:8000/feedback", json=payload, timeout=10)
                        response.raise_for_status()
                        st.success(response.json().get("message", "Feedback submitted!"))
                        # Clear the displayed interaction after submitting feedback
                        st.session_state.last_interaction_for_feedback = None
                    except Exception as e:
                        st.error(f"Failed to submit feedback: {sanitize_for_display(str(e))}")
        else:
            st.info("Click 'Load Last Interaction for Feedback' to see details of the last AI output and provide your rating.")
            # The button to load is already present above this section.


if __name__ == "__main__":
    main()