# dashboard.py
import streamlit as st

def main():
    """
    The main function for the Streamlit dashboard.
    """
    st.set_page_config(
        page_title="The Giblet Dashboard",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 The Giblet: Your Personal AI Dev Companion")
    st.write("Welcome to the visual canvas for your AI partner. This dashboard will grow to visualize your project's roadmap, history, and creative sessions.")

    st.info("This is the first version of the dashboard. More features coming soon!", icon="ℹ️")

if __name__ == "__main__":
    main()