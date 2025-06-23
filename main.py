# main.py
import os
os.environ['PYTHONUTF8'] = '1' # Force Python to use UTF-8 mode
os.environ['GIT_PYTHON_GIT_OPTIONS'] = '-c color.ui=false' # Helps with Git output parsing 

from dotenv import load_dotenv # Import load_dotenv
load_dotenv() # Load environment variables from .env file
from ui.cli import start_cli_loop
from core.logger_setup import setup_logger

def main():
    """
    Main entrypoint for The Giblet.
    Initializes logging and starts the interactive CLI session.
    """
    setup_logger()
    start_cli_loop()

if __name__ == "__main__":
    main()