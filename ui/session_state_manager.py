import streamlit as st

def initialize_session_state():
    """
    Initializes all necessary session state variables for the Streamlit dashboard.
    This ensures that state persists across reruns and is set up correctly on first load.
    """
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "🧬 Genesis Mode"
    if 'agent_plan' not in st.session_state:
        st.session_state.agent_plan = None
    if 'agent_execution_result' not in st.session_state:
        st.session_state.agent_execution_result = None
    if 'genesis_conversation' not in st.session_state:
        st.session_state.genesis_conversation = []
    if 'genesis_session_active' not in st.session_state:
        st.session_state.genesis_session_active = False
    if 'genesis_final_brief' not in st.session_state:
        st.session_state.genesis_final_brief = None
    if 'generated_readme' not in st.session_state:
        st.session_state.generated_readme = None
    if 'generated_roadmap' not in st.session_state:
        st.session_state.generated_roadmap = None
    if 'duplication_report' not in st.session_state:
        st.session_state.duplication_report = None
    if 'original_code_refactor' not in st.session_state:
        st.session_state.original_code_refactor = None
    if 'refactored_code_refactor' not in st.session_state:
        st.session_state.refactored_code_refactor = None
    if 'refactor_explanation' not in st.session_state:
        st.session_state.refactor_explanation = None
    if 'explorer_source' not in st.session_state:
        st.session_state.explorer_source = "Local Filesystem"
    if 'explorer_files' not in st.session_state:
        st.session_state.explorer_files = []
    if 'explorer_github_owner' not in st.session_state:
        st.session_state.explorer_github_owner = ""
    if 'explorer_github_repo' not in st.session_state:
        st.session_state.explorer_github_repo = ""
    if 'explorer_selected_file_content' not in st.session_state:
        st.session_state.explorer_selected_file_content = None
    if 'explorer_selected_file_path' not in st.session_state:
        st.session_state.explorer_selected_file_path = None