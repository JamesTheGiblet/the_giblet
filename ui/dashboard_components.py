# ui/dashboard_components.py
import streamlit as st

def render_sidebar_navigation():
    """
    Renders the sidebar navigation for the dashboard.
    Sets st.session_state.active_tab based on button clicks.
    """
    st.header("🚀 Quick Actions")
    tab_names = [
        "🏠 Home",                # New Home/Overview tab
        "🧬 Genesis Mode",        # High-level project creation
        "🗺️ Roadmap",             # High-level project view
        "📂 File Explorer",       # Core utility for browsing
        "🛠️ Code Agent",          # Core "doing" tasks
        "✨ Refactor",            # Core "doing" tasks
        "🔬 Code Analysis",       # Analysis and review
        "🤖 Automation",         # Project-level tasks
        "👤 Profile",             # User-specific settings
        "🎨 My Vibe"              # Project-specific settings
    ]

    # Get the current active tab's index to set the default for the radio button
    tab_titles = tab_names
    try:
        current_index = tab_titles.index(st.session_state.active_tab)
    except ValueError:
        current_index = 0 # Default to the first tab if not found

    st.write("## Navigation")
    
    active_tab = st.radio(
        "Choose a section:",
        tab_titles,
        index=current_index,
        help="Navigate between the different sections of the dashboard.",
        key="main_nav_radio"
    )

    # If the user selects a new tab, update the session state and rerun
    if active_tab != st.session_state.active_tab:
        st.session_state.active_tab = active_tab
        st.rerun()