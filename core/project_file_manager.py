import os
import logging
from core.giblet_config import giblet_config # Import giblet_config
from typing import Dict, Any

class ProjectFileManager:
    """
    Manages the creation and saving of project-related files to the local file system.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_project_directory(self, project_name: str, base_path: str = ".") -> str:
        """
        Creates a new directory for the project.

        Args:
            project_name: The name of the project, used as the directory name.
            base_path: The base path where the project directory should be created.

        Returns:
            The full path to the created project directory.
        """
        project_path = os.path.join(giblet_config.get_project_root(), project_name.replace(" ", "_").lower())
        try:
            os.makedirs(project_path, exist_ok=True)
            self.logger.info(f"Created project directory: {project_path}")
            return project_path
        except OSError as e:
            self.logger.error(f"Error creating project directory {project_path}: {e}")
            raise

    def save_file(self, file_path: str, content: str):
        """
        Saves content to a specified file path.
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info(f"Saved file: {file_path}")
        except IOError as e:
            self.logger.error(f"Error saving file {file_path}: {e}")
            raise