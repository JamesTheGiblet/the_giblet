# dashboard.py
import streamlit as st
import sys
from pathlib import Path

# This line ensures that the script can find your 'core' modules
sys.path.append(str(Path(__file__).parent))

from core.roadmap_manager import RoadmapManager
from core.git_analyzer import GitAnalyzer
from core.idea_synth import IdeaSynthesizer # <<< NEW IMPORT (for clarity)
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

    st.title("🧠 The Giblet: Project Dashboard")

    # --- Instantiate Core Modules ---
    # The dashboard runs as a separate process, so it creates its own instances.
    try:
        memory = Memory()
        roadmap_manager = RoadmapManager(memory_system=memory)
        git_analyzer = GitAnalyzer()
        idea_synth = IdeaSynthesizer() # <<< NEW
    except Exception as e:
        st.error(f"Failed to initialize core modules: {e}")
        return

    # --- Create a tabbed interface ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Roadmap", "📜 History", "🎨 Creative"])

    with tab1:
        # --- Roadmap Visualization ---
        st.header("Project Roadmap")
        tasks = roadmap_manager.get_tasks()
        if not tasks:
            st.warning("No tasks found in roadmap.md")
        else:
            # Group tasks by phase for a cleaner look
            phases = {}
            current_phase = "General Tasks"
            for task in tasks:
                # A simple way to detect a phase header
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

    with tab2:
        # --- Git History Visualization ---
        st.header("Recent Project History")
        if not git_analyzer.repo:
            st.warning("Not a Git repository. History cannot be displayed.")
        else:
            log = git_analyzer.get_commit_log(max_count=15)
            if not log:
                st.warning("No Git history found.")
            else:
                for commit in log:
                    st.markdown(f"**Commit:** `{commit['sha']}`")
                    st.text(f"Author: {commit['author']} | Date: {commit['date']}")
                    st.info(f"{commit['message']}", icon="💬")
                    st.divider()

    # <<< NEW: Creative Playground Tab
    with tab3:
        st.header("Idea Synthesizer Playground")

        prompt_text = st.text_area("Enter your prompt or idea to explore:", height=150)

        weird_mode = st.toggle("Enable Weird Mode 🤪")

        if st.button("Generate Ideas", use_container_width=True):
            if not prompt_text:
                st.warning("Please enter a prompt to generate ideas.")
            elif not idea_synth.model:
                st.error("Idea Synthesizer is not available. Check API key and configuration.")
            else:
                with st.spinner("The Giblet is brainstorming..."):
                    response = idea_synth.generate_ideas(prompt_text, weird_mode=weird_mode)
                    st.markdown("---")
                    st.markdown(response)

if __name__ == "__main__":
    main()