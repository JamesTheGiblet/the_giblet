# core/logger_setup.py
import logging
from pathlib import Path

def setup_logger():
    """Configures the root logger to save detailed logs to a file."""
    log_dir = Path(__file__).parent.parent / "data"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "giblet_debug.log"

    # Create a file handler
    # 'w' mode will overwrite the log each time, 'a' mode would append.
    handler = logging.FileHandler(log_file, mode='w')
    
    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add the handler to the root logger
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    
    print("📝 Logging configured. Debug output will be saved to data/giblet_debug.log")