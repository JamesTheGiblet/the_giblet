# In main.py
from ui.cli import start_cli_loop
from core.logger_setup import setup_logger # <<< NEW IMPORT

def main():
    """
    Main entrypoint for The Giblet.
    Initializes logging and starts the interactive CLI session.
    """
    setup_logger() # <<< NEW: Set up our logger on startup
    start_cli_loop()

if __name__ == "__main__":
    main()