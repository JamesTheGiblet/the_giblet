# dashboard.py
import streamlit as st
import httpx
import sys
import os
import difflib # <<< NEW IMPORT at the top
from pathlib import Path
import json # Add this
import shlex # For parsing plan steps
import subprocess # For launching the gauntlet editor

# This line ensures that the script can find your 'core' modules
sys.path.append(str(Path(__file__).parent))

from core.roadmap_manager import RoadmapManager
from core.git_analyzer import GitAnalyzer
from core.idea_synth import IdeaSynthesizer
from core.memory import Memory
from core.user_profile import UserProfile, DEFAULT_PROFILE_STRUCTURE # Ensure UserProfile is imported
from core.llm_provider_base import LLMProvider # Import base provider
from core.llm_providers import GeminiProvider, OllamaProvider # Import specific providers
from core.code_generator import CodeGenerator # For CapabilityAssessor
from core.capability_assessor import CapabilityAssessor # For the new UI feature

# --- Proactive Learner Imports (from snippet) ---
try:
    # Assuming ProactiveLearner is in the_giblet.core
    from core.proactive_learner import ProactiveLearner, UserProfilePlaceholder
    # from core.user_profile import UserProfile # Ideal future import if UserProfilePlaceholder is not used
except ImportError as e:
    st.error(f"Critical Import Error (ProactiveLearner): {e}. Dashboard features relying on this module may fail.")
    # Fallback for ProactiveLearner and UserProfilePlaceholder
    class ProactiveLearner: pass
    class UserProfilePlaceholder: pass

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

# --- New Tab Function (from snippet) ---
def show_proactive_suggestions_tab():
    st.header("🧠 Proactive Learning & Suggestions")
    st.write("""
        The Giblet analyzes your feedback and profile settings to offer suggestions
        for improving prompt templates or agent behaviors.
    """)

    if ProactiveLearner.__name__ == "ProactiveLearner" and ProactiveLearner.__module__ == "__main__": # Check if fallback was used
        st.error("ProactiveLearner module could not be loaded. Suggestions feature is unavailable.")
        return

    if st.button("🔍 Get Proactive Suggestions", key="get_proactive_suggestions_btn"):
        try:
            # Note: UserProfilePlaceholder loads "data/user_profile.json" relative to CWD.
            # Ensure this file exists or is created by UserProfile logic.
            # Ideally, this would use the main UserProfile from core.user_profile
            # For now, using the placeholder as per the snippet's design.
            user_profile_placeholder_instance = UserProfilePlaceholder()
            learner = ProactiveLearner(user_profile_placeholder_instance)
            
            with st.spinner("Analyzing feedback and profile..."):
                suggestions = learner.generate_suggestions()

            if suggestions:
                st.subheader("Here are some suggestions for you:")
                for i, suggestion in enumerate(suggestions):
                    if "No specific proactive suggestions" in suggestion and len(suggestions) == 1:
                        st.success(suggestion) 
                    else:
                        st.info(f"{i+1}. {suggestion}")
        except Exception as e:
            st.error(f"Error generating suggestions: {sanitize_for_display(str(e))}")
            st.caption("Please ensure 'data/user_profile.json' is accessible from the directory where Streamlit is run, and that it's a valid JSON file.")

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

    # Helper function to get the configured LLM provider for Dashboard
    def get_dashboard_llm_provider(profile: UserProfile) -> LLMProvider | None:
        active_provider_name = profile.get_preference("llm_provider_config", "active_provider", "gemini")
        raw_provider_configs = profile.get_preference("llm_provider_config", "providers")

        provider_configs = {}
        if isinstance(raw_provider_configs, dict):
            provider_configs = raw_provider_configs
        elif isinstance(raw_provider_configs, str) and raw_provider_configs.startswith("{") and raw_provider_configs.endswith("}"): # Basic check for JSON string
            try:
                provider_configs = json.loads(raw_provider_configs) # Attempt to parse if it's a stringified JSON
            except json.JSONDecodeError:
                # print(f"⚠️ Dashboard: Could not parse 'providers' config string from profile. Using defaults. String was: {raw_provider_configs}") # Can be noisy
                provider_configs = DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]
        else: # Not a dict, not a parsable string, or None
            provider_configs = DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"] # Fallback to default structure

        if active_provider_name == "gemini":
            gemini_config = provider_configs.get("gemini", {})
            api_key = gemini_config.get("api_key")
            model_name = gemini_config.get("model_name", "gemini-1.5-flash-latest")
            # print(f"Dashboard: Configuring GeminiProvider (model: {model_name}, API key from profile: {'yes' if api_key else 'no/use .env'})") # Can be noisy
            return GeminiProvider(model_name=model_name, api_key=api_key if api_key else None)
        elif active_provider_name == "ollama":
            ollama_config = provider_configs.get("ollama", {})
            base_url = ollama_config.get("base_url", "http://localhost:11434")
            model_name = ollama_config.get("model_name", "mistral")
            # print(f"Dashboard: Configuring OllamaProvider (model: {model_name}, url: {base_url})") # Can be noisy
            return OllamaProvider(model_name=model_name, base_url=base_url)
        else:
            # print(f"⚠️ Dashboard: Unknown LLM provider '{active_provider_name}' configured. Defaulting to Gemini.") # Can be noisy
            return GeminiProvider()

    dashboard_llm_provider = get_dashboard_llm_provider(user_profile_instance)

    if not dashboard_llm_provider or not dashboard_llm_provider.is_available():
        st.sidebar.warning(f"Configured LLM provider ({dashboard_llm_provider.PROVIDER_NAME if dashboard_llm_provider else 'N/A'}) is not available. Dashboard LLM features may be limited.")

    # --- Sidebar ---
    with st.sidebar:
        st.header("🚀 Quick Actions")
        
        tab_names = ["🗺️ Roadmap", "📜 History", "🛠️ Generator", "✨ Refactor", "📂 File Explorer", "🤖 Automation", "👤 Profile", "🧠 Proactive Suggestions"] # Added new tab
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = tab_names[0] # Default to the first tab

        for tab_name in tab_names:
            if st.button(tab_name, key=f"sidebar_nav_{tab_name.replace(' ', '_')}", use_container_width=True):
                st.session_state.active_tab = tab_name
                st.rerun()
        
        st.divider()
        
        # You can add other quick actions or focus management tools here if needed
        # For example:
        # st.subheader("🎯 Current Focus")
        # ... focus management UI ...
        # st.divider()
        # st.subheader("⚡ Quick Tools")
        # ... idea/plan generation expanders ...

    st.title("🧠 The Giblet: Project Cockpit")
 
    # --- Main Tab Navigation ---
    # The st.radio navigation is now removed from the main panel.
    # The active tab is controlled by st.session_state.active_tab, set by sidebar buttons.
    
    # Ensure active_tab is initialized if it somehow got removed from session_state
    all_tab_options = ["🗺️ Roadmap", "📜 History", "🛠️ Generator", "✨ Refactor", "📂 File Explorer", "🤖 Automation", "👤 Profile", "🧠 Proactive Suggestions"] # Added new tab
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = all_tab_options[0]
    elif st.session_state.active_tab not in all_tab_options: # If active_tab is an invalid old value
        st.session_state.active_tab = all_tab_options[0]

    # --- Tab Content ---
    # The content display logic remains the same, using if/elif based on st.session_state.active_tab
    if st.session_state.active_tab == "🗺️ Roadmap":
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
            st.error(f"Error in Roadmap section: {sanitize_for_display(str(e))}")
    elif st.session_state.active_tab == "📜 History":
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
    elif st.session_state.active_tab == "🛠️ Generator":
        # The Generator tab requires its own instances
        try:
            # Pass the dashboard's user_profile, memory, and llm_provider instances
            idea_synth = IdeaSynthesizer(user_profile=user_profile_instance, memory_system=memory_instance, llm_provider=dashboard_llm_provider)
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
            
            # Define some icons for common commands
            command_icons = {
                "write": "📝",
                "generate": "💡",
                "exec": "⚙️",
                "skill": "🧠",
                "refactor": "✨",
                "plan": "🗺️",
                "default": "▶️"
            }

            for i, step_string in enumerate(st.session_state.agent_plan, 1):
                parts = shlex.split(step_string)
                command_name = parts[0] if parts else "Unknown"
                args_display = " ".join(parts[1:]) if len(parts) > 1 else ""
                icon = command_icons.get(command_name, command_icons["default"])

                col1, col2, col3 = st.columns([0.05, 0.3, 0.65])
                with col1: st.markdown(f"**{i}.**")
                with col2: st.markdown(f"{icon} `{command_name}`")
                with col3: st.code(args_display, language=None) # Use st.code for better display of args
            
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
        # Removed the 'elif st.session_state.agent_execution_result:' here as it was causing an error if 'e' wasn't defined in this scope.

    # <<< NEW: Refactor Cockpit Tab
    elif st.session_state.active_tab == "✨ Refactor":
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
    elif st.session_state.active_tab == "📂 File Explorer":
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
    elif st.session_state.active_tab == "🤖 Automation":
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

    elif st.session_state.active_tab == "👤 Profile": # Profile Tab
        st.header("👤 User Profile & Settings")

        # Function to fetch profile data
        def fetch_profile():
            try:
                response = httpx.get("http://localhost:8000/profile", timeout=10)
                response.raise_for_status()
                data = response.json().get("profile", {})
                st.session_state.user_profile_data = data
            except Exception as e_prof:
                st.error(f"Failed to fetch profile: {sanitize_for_display(str(e_prof))}")
                st.session_state.user_profile_data = {}

        # Helper to update profile via API and refresh
        def update_profile_setting(category, key, value):
            try:
                payload = {"category": category, "key": key, "value": str(value)} # Ensure value is string for API
                response = httpx.post("http://localhost:8000/profile/set", json=payload, timeout=10)
                response.raise_for_status()
                fetch_profile() # Refresh profile data in session state
                st.toast(f"Profile setting '{category}.{key}' updated!", icon="🎉")
                return True
            except Exception as e:
                st.error(f"Failed to update {category}.{key}: {sanitize_for_display(str(e))}")
                return False

        if 'user_profile_data' not in st.session_state:
            fetch_profile()

        st.subheader("Current User Profile")
        if st.session_state.get('user_profile_data'):
            st.json(st.session_state.user_profile_data)
        else:
            st.info("No profile data loaded or profile is empty.")
        
        if st.button("Refresh Profile Data", key="refresh_profile_data_btn"):
            fetch_profile()

        st.divider()
        st.subheader("Set/Update Preference")
        with st.form("set_preference_form"):
            pref_category = st.text_input("Category (e.g., general, coding_style, llm_settings)")
            pref_key = st.text_input("Key (e.g., user_name, indent_size, idea_synth_persona)")
            pref_value = st.text_input("Value")
            submitted_pref = st.form_submit_button("Set Preference")

            if submitted_pref:
                if pref_category and pref_key: # Value can be empty string
                    update_profile_setting(pref_category, pref_key, pref_value)
                else:
                    st.warning("Category and Key are required to set a preference.")
        
        st.divider()
        st.subheader("AI Vibe & Behavior Settings")

        # IdeaSynthesizer Settings
        st.markdown("##### Idea Synthesizer")
        idea_personas = ["creative and helpful", "analytical and detailed", "concise and direct", "slightly sarcastic but brilliant", "formal academic researcher", "Custom"]
        current_idea_persona = st.session_state.get('user_profile_data', {}).get("llm_settings", {}).get("idea_synth_persona", idea_personas[0])
        
        selected_idea_persona_idx = idea_personas.index(current_idea_persona) if current_idea_persona in idea_personas else idea_personas.index("Custom")
        selected_idea_persona = st.selectbox(
            "Persona", options=idea_personas, 
            index=selected_idea_persona_idx, 
            key="idea_persona_select"
        )
        custom_idea_persona_val = current_idea_persona if selected_idea_persona_idx == idea_personas.index("Custom") else ""
        if selected_idea_persona == "Custom":
            custom_idea_persona_val = st.text_input("Enter Custom Idea Persona:", value=custom_idea_persona_val, key="custom_idea_persona_input")
        
        final_idea_persona = custom_idea_persona_val if selected_idea_persona == "Custom" else selected_idea_persona
        if final_idea_persona != current_idea_persona: # Check if there's a change to save
            if update_profile_setting("llm_settings", "idea_synth_persona", final_idea_persona):
                 st.success(f"IdeaSynthesizer Persona updated to: {final_idea_persona}")

        current_creativity = int(st.session_state.get('user_profile_data', {}).get("llm_settings", {}).get("idea_synth_creativity", 3))
        new_creativity = st.slider("Creativity Level (1=Practical, 5=Experimental)", 1, 5, current_creativity, key="idea_creativity_slider")
        if new_creativity != current_creativity:
            if update_profile_setting("llm_settings", "idea_synth_creativity", new_creativity):
                st.success(f"IdeaSynthesizer Creativity updated to: {new_creativity}")

        # Placeholder for CodeGenerator Persona (similar logic)
        st.markdown("##### Code Generator")
        st.caption("Code Generator persona settings can be added here.")

        st.divider()
        st.subheader("LLM Provider Configuration")

        llm_provider_config = st.session_state.get('user_profile_data', {}).get("llm_provider_config", {})
        active_provider = llm_provider_config.get("active_provider", "gemini")
        
        # Robust handling for providers_settings in the UI
        raw_providers_settings_ui = llm_provider_config.get("providers")
        providers_settings = {}
        if isinstance(raw_providers_settings_ui, dict):
            providers_settings = raw_providers_settings_ui
        elif isinstance(raw_providers_settings_ui, str) and raw_providers_settings_ui.startswith("{") and raw_providers_settings_ui.endswith("}"):
            try:
                providers_settings = json.loads(raw_providers_settings_ui)
            except json.JSONDecodeError:
                st.warning("Could not parse LLM provider settings from profile for UI. Using defaults.")
                providers_settings = DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]
        else:
            providers_settings = DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]

        new_active_provider = st.selectbox(
            "Active LLM Provider", 
            options=["gemini", "ollama"], 
            index=["gemini", "ollama"].index(active_provider),
            key="llm_active_provider_select"
        )
        if new_active_provider != active_provider:
            if update_profile_setting("llm_provider_config", "active_provider", new_active_provider):
                st.success(f"Active LLM Provider set to {new_active_provider}. Restart Giblet for changes to fully apply.")
                # No need to st.rerun() here as update_profile_setting calls fetch_profile which updates session_state

        st.markdown("###### Gemini Settings")
        gemini_settings = providers_settings.get("gemini", {})
        gemini_api_key = st.text_input("Gemini API Key (optional, uses .env if blank)", value=gemini_settings.get("api_key", ""), type="password", key="gemini_api_key_input")
        gemini_model = st.text_input("Gemini Model Name", value=gemini_settings.get("model_name", "gemini-1.5-flash-latest"), key="gemini_model_input")

        if gemini_api_key != gemini_settings.get("api_key", "") or gemini_model != gemini_settings.get("model_name", "gemini-1.5-flash-latest"):
            updated_gemini_config = {"api_key": gemini_api_key, "model_name": gemini_model}
            new_providers_settings = providers_settings.copy()
            new_providers_settings["gemini"] = updated_gemini_config
            if update_profile_setting("llm_provider_config", "providers", new_providers_settings): # Save the whole 'providers' dict
                st.success("Gemini settings updated.")

        st.markdown("###### Ollama Settings")
        ollama_settings = providers_settings.get("ollama", {})
        ollama_base_url = st.text_input("Ollama Base URL", value=ollama_settings.get("base_url", "http://localhost:11434"), key="ollama_url_input")
        ollama_model = st.text_input("Ollama Model Name", value=ollama_settings.get("model_name", "mistral"), key="ollama_model_input")

        if ollama_base_url != ollama_settings.get("base_url", "") or ollama_model != ollama_settings.get("model_name", "mistral"):
            updated_ollama_config = {"base_url": ollama_base_url, "model_name": ollama_model}
            new_providers_settings = providers_settings.copy() # Get a fresh copy
            new_providers_settings["ollama"] = updated_ollama_config
            if update_profile_setting("llm_provider_config", "providers", new_providers_settings): # Save the whole 'providers' dict
                st.success("Ollama settings updated.")

        st.divider()
        st.subheader("🔬 LLM Capability Assessment (Gauntlet)")
        st.caption("Run a series of tests against the currently configured LLM to assess its capabilities.")

        if 'gauntlet_results' not in st.session_state:
            st.session_state.gauntlet_results = None

        if st.button("Run LLM Capability Gauntlet", key="run_gauntlet_btn"):
            st.session_state.gauntlet_results = None # Clear previous results
            if not dashboard_llm_provider or not dashboard_llm_provider.is_available():
                st.error("Cannot run assessment: The configured LLM provider is not available.")
            else:
                with st.spinner(f"Running Capability Gauntlet on {dashboard_llm_provider.PROVIDER_NAME} ({dashboard_llm_provider.model_name})... This may take some time."):
                    try:
                        # Instantiate necessary components for the assessor
                        # These use the dashboard's configured LLM provider
                        cg_for_assessment = CodeGenerator(user_profile=user_profile_instance, memory_system=memory_instance, llm_provider=dashboard_llm_provider)
                        is_for_assessment = IdeaSynthesizer(user_profile=user_profile_instance, memory_system=memory_instance, llm_provider=dashboard_llm_provider)
                        
                        assessor = CapabilityAssessor(llm_provider=dashboard_llm_provider, code_generator=cg_for_assessment, idea_synthesizer=is_for_assessment)
                        st.session_state.gauntlet_results = assessor.run_gauntlet()
                        st.success("Capability Gauntlet finished!")

                        # Save the gauntlet results to UserProfile
                        if st.session_state.gauntlet_results:
                            profile_data = st.session_state.gauntlet_results
                            provider_name = profile_data.get("provider_name")
                            model_name = profile_data.get("model_name")
                            if provider_name and model_name and user_profile_instance:
                                user_profile_instance.save_gauntlet_profile(provider_name, model_name, profile_data)
                                st.toast(f"Gauntlet profile saved for {provider_name}/{model_name}!", icon="💾")

                    except Exception as e_gauntlet:
                        st.error(f"An error occurred during the Gauntlet run: {sanitize_for_display(str(e_gauntlet))}")
        
        if st.session_state.gauntlet_results:
            st.json(st.session_state.gauntlet_results)

        if st.button("✏️ Edit Gauntlet Tests", key="edit_gauntlet_tests_btn"):
            st.info("Attempting to launch the Gauntlet Test Editor in a new process...")
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", "gauntlet_editor.py"])
            st.caption("If the editor doesn't open, ensure Streamlit is installed and `gauntlet_editor.py` is in the project root.")

        st.divider()
        st.subheader("Feedback on Last AI Interaction")
        # Fetch last interaction
        if 'last_ai_interaction' not in st.session_state:
            st.session_state.last_ai_interaction = None
        
        if st.button("Load Last AI Interaction for Feedback"):
            try:
                response = httpx.get("http://localhost:8000/feedback/last_interaction", timeout=5)
                response.raise_for_status()
                st.session_state.last_ai_interaction = response.json().get("interaction")
            except Exception as e_feedback_load:
                st.error(f"Could not load last interaction: {sanitize_for_display(str(e_feedback_load))}")

        if st.session_state.last_ai_interaction:
            st.json(st.session_state.last_ai_interaction)
            feedback_rating = st.selectbox("Rate this interaction:", ["", "positive", "neutral", "negative"], key="feedback_rating")
            feedback_comment = st.text_area("Additional comments:", key="feedback_comment")
            if st.button("Submit Feedback", key="submit_feedback_btn"):
                if feedback_rating:
                    try:
                        payload = {"rating": feedback_rating, "comment": feedback_comment}
                        response = httpx.post("http://localhost:8000/feedback", json=payload, timeout=10)
                        response.raise_for_status()
                        st.success(response.json().get("message", "Feedback submitted!"))
                        st.session_state.last_ai_interaction = None # Clear after submitting
                    except Exception as e_feedback_submit:
                        st.error(f"Failed to submit feedback: {sanitize_for_display(str(e_feedback_submit))}")
                else:
                    st.warning("Please select a rating.")
        else:
            st.info("No recent AI interaction loaded for feedback, or feedback already submitted.")

        st.divider()
        st.subheader("Clear Profile")
        if st.button("Clear Entire User Profile", type="secondary", key="clear_profile_btn"):
            try:
                response = httpx.post("http://localhost:8000/profile/clear", timeout=10)
                response.raise_for_status()
                st.success(response.json().get("message", "Profile cleared!"))
                fetch_profile() # Refresh to show empty profile
            except Exception as e_clear:
                st.error(f"Failed to clear profile: {sanitize_for_display(str(e_clear))}")

    elif st.session_state.active_tab == "🧠 Proactive Suggestions":
        show_proactive_suggestions_tab()

if __name__ == "__main__":
    main()