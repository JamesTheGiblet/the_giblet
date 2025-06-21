# ui/dashboard_components.py
import streamlit as st

def render_sidebar_navigation():
    """
    Renders the sidebar navigation for the dashboard.
    Sets st.session_state.active_tab based on button clicks.
    """
    st.header("🚀 Quick Actions")
    tab_names = [
        "🧬 Genesis Mode",
        "🗺️ Roadmap",
        "🛠️ Agent & Generator",
        "✨ Refactor",
        "📂 File Explorer",
        "🤖 Automation",
        "🔬 Code Analysis",
        "👤 Profile",
        "🎨 My Vibe"
    ]

    for tab_name in tab_names:
        if st.button(tab_name, key=f"sidebar_nav_{tab_name.replace(' ', '_')}", use_container_width=True):
            st.session_state.active_tab = tab_name
            st.rerun()