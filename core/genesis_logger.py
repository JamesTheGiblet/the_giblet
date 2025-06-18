# core/genesis_logger.py

"""
Manages logging for projects created via Genesis Mode.

This module handles initializing, writing to, and reading from
genesis_log.json, which tracks metadata for every project
created using The Giblet's Genesis Mode.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GenesisLogger:
    """
    Manages the log of projects created via Genesis Mode.
    """

    def __init__(self, file_path: Optional[Path] = None):
        """
        Initializes the GenesisLogger.

        Args:
            file_path: Optional path to the genesis log JSON file.
                       If None, uses a default path within the project's data directory.
        """
        if file_path is None:
            # Assuming this file is in core/, so ../data/
            base_dir = Path(__file__).resolve().parent.parent
            self.file_path: Path = base_dir / "data" / "genesis_log.json"
        else:
            self.file_path: Path = file_path

        self.log_entries: List[Dict[str, Any]] = []
        self._load_log()

    def _ensure_file_exists(self) -> None:
        """Ensures the log file and its directory exist, creating them if necessary."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                logger.info(f"Genesis log file not found at {self.file_path}. Initializing with an empty log.")
                self._save_log() # Save an empty list to create the file
        except IOError as e:
            logger.error(f"Error ensuring genesis log file exists at {self.file_path}: {e}")

    def _load_log(self) -> None:
        """Loads log entries from the JSON file."""
        self._ensure_file_exists()
        if not self.file_path.exists(): # Should be created by _ensure_file_exists
             logger.warning(f"Log file {self.file_path} still does not exist after attempting creation. Using in-memory empty log.")
             self.log_entries = []
             return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Handle empty file case
                content = f.read()
                if not content.strip():
                    self.log_entries = []
                else:
                    self.log_entries = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.file_path}. Treating as empty log. Please check the file.")
            self.log_entries = [] # Avoid overwriting potentially recoverable data by not saving here
        except IOError as e:
            logger.error(f"Could not read genesis log file {self.file_path}: {e}. Using empty log.")
            self.log_entries = []

    def _save_log(self) -> None:
        """Saves the current log entries to the JSON file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.log_entries, f, indent=4)
        except IOError as e:
            logger.error(f"Could not write genesis log file {self.file_path}: {e}")

    def log_project_creation(
        self,
        project_name: str,
        initial_brief: str,
        genesis_settings_used: Dict[str, Any],
        workspace_type: str, # e.g., "local", "github"
        workspace_location: str, # path or URL
        entropy_level: Optional[float] = None, # For random genesis
        generated_readme_path: Optional[str] = None,
        generated_roadmap_path: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Adds a new project creation entry to the log.
        """
        log_entry = {
            "project_name": project_name,
            "timestamp": datetime.now().isoformat(),
            "initial_brief": initial_brief,
            "genesis_settings_used": genesis_settings_used, # Could include style prefs active at creation
            "workspace_type": workspace_type,
            "workspace_location": workspace_location,
            "entropy_level": entropy_level,
            "generated_readme_path": generated_readme_path,
            "generated_roadmap_path": generated_roadmap_path,
            "metadata": additional_metadata if additional_metadata else {}
        }
        self.log_entries.append(log_entry)
        self._save_log()
        logger.info(f"Logged creation of project: {project_name}")

    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Returns a copy of all log entries."""
        return self.log_entries.copy()

# Example Usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test with a temporary file
    temp_log_file = Path("./temp_genesis_log.json")
    if temp_log_file.exists():
        temp_log_file.unlink() # Clean up before test

    logger_instance = GenesisLogger(file_path=temp_log_file)

    print("Initial log entries:", logger_instance.get_all_logs())

    logger_instance.log_project_creation(
        project_name="Plant Whisperer App",
        initial_brief="An app that lets plants text their owners when thirsty.",
        genesis_settings_used={"readme_style": "detailed", "roadmap_format": "phase_based", "tone": "witty"},
        workspace_type="local",
        workspace_location="./my_projects/plant_whisperer",
        generated_readme_path="plant_whisperer/README.md",
        additional_metadata={"primary_language_guess": "python"}
    )

    logger_instance.log_project_creation(
        project_name="Cosmic Ray Visualizer",
        initial_brief="A tool to visualize cosmic ray data.",
        genesis_settings_used={"readme_style": "standard", "repo_visibility": "public"},
        workspace_type="github",
        workspace_location="https://github.com/user/cosmic_ray_viz",
        entropy_level=0.75 # Example for a random genesis feature
    )

    print("\nLog entries after adding projects:", json.dumps(logger_instance.get_all_logs(), indent=2))

    # Test loading existing log
    reloaded_logger = GenesisLogger(file_path=temp_log_file)
    print("\nLog entries after reloading:", json.dumps(reloaded_logger.get_all_logs(), indent=2))

    # Clean up the temporary file
    if temp_log_file.exists():
        temp_log_file.unlink()