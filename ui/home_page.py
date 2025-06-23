# ui/home_page.py
import streamlit as st

def render():
    """Renders the Home page content for the Giblet dashboard."""

    st.header("Welcome to The Giblet: Your AI-Powered Development Cockpit 🧠")
    st.markdown("""
    This dashboard is the central control system for **The Giblet**, an autonomous agent designed to help you plan, build, and manage software projects. It acts as both a window into the agent's operations and a powerful set of tools for you to interact with.
    """)

    st.info("**Getting Started:** Navigate through the tabs in the left sidebar to access different features.", icon="👈")

    st.divider()

    st.subheader("How It Works: The Core Workflow")
    st.markdown("""
    The Giblet is built around a core philosophy: **Idea -> Plan -> Build -> Automate**.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧬 Genesis Mode")
        st.write("""
        This is where every new project begins. Provide a high-level idea, and the **Idea Interpreter** will engage in a dialogue with you to flesh it out into a comprehensive project brief, complete with a README and a task-based roadmap.
        
        - **Start with an idea**: Simple or complex, just type it in.
        - **Answer questions**: The agent clarifies requirements.
        - **Get a plan**: Receive a detailed brief, README, and `roadmap.md`.
        """)

    with col2:
        st.subheader("🗺️ Project Roadmap")
        st.write("""
        Once a project is planned, this tab gives you a live look at the `roadmap.md` file in your project. It visualizes the phases and tasks, showing what's planned and what's complete. It's a simple, clear view of your project's progress.
        
        - **Visualize tasks**: See all planned tasks from your roadmap.
        - **Track progress**: Completed tasks are checked off automatically.
        """)

    st.divider()
    
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🛠️ Agent & Generator")
        st.write("""
        This is the powerhouse. Give the autonomous agent a high-level goal (e.g., "implement the user login feature"). It will:
        
        1.  **Create a plan** of shell commands and code generation steps.
        2.  **Execute the plan**, writing code, running tests, and even attempting to fix its own errors.
        3.  **Report the results** of its work.
        """)

    with col4:
        st.subheader("🤖 Automation & Analysis")
        st.write("""
        The Giblet includes tools to handle repetitive tasks and maintain code quality.
        
        - **File Explorer**: Browse local and GitHub files.
        - **Code Analysis**: Find duplicate and overly complex code.
        - **Refactor**: Ask the agent to refactor code with specific instructions.
        - **Automation**: Generate changelogs, add TODO stubs, and more.
        """)

    st.divider()

    st.success("""
    **Your Role is Strategic:** You provide the vision and the high-level goals. The Giblet handles the tedious, step-by-step execution, freeing you up to focus on the bigger picture of your project's development.
    """, icon="🚀")

