# main.py
import os
os.environ['PYTHONUTF8'] = '1' # Force Python to use UTF-8 mode
os.environ['GIT_PYTHON_GIT_OPTIONS'] = '-c color.ui=false' # Helps with Git output parsing 
import logging
import json
import argparse # Added for command-line argument parsing
import sys # Added for system-level operations like sys.exit
from dotenv import load_dotenv # Import load_dotenv
load_dotenv() # Load environment variables from .env file
from ui.cli import start_cli_loop
from core.roadmap_manager import RoadmapManager
from core.logger_setup import setup_logger
from core.giblet_config import giblet_config # Import the GibletConfig singleton

def main():
    """
    Main entrypoint for The Giblet.
    Initializes logging and starts the interactive CLI session.
    """
    setup_logger()

    # Argument parsing for project root
    parser = argparse.ArgumentParser(description="The Giblet: Your Personal AI Dev Companion")
    parser.add_argument(
        "--project-root",
        type=str,
        help="Specify the root directory of The Giblet project. "
             "This is where roadmap.md, README.md, and other data files are located."
    )
    args = parser.parse_args()

    try:
        if args.project_root:
            giblet_config.set_project_root(args.project_root)
        else:
            # Initialize default project root if not set via argument.
            # This call will set the default if _project_root is None.
            giblet_config.get_project_root()

        print(f"Current Giblet project root: {giblet_config.get_project_root()}")

        # Example of using the configured path for RoadmapManager
        roadmap_manager = RoadmapManager()
        if roadmap_manager.load_roadmap():
            print("Roadmap loaded successfully.")
            # Further operations with roadmap_manager...
        else:
            print("Failed to load roadmap.")

        start_cli_loop()
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()