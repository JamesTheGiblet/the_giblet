# core/project_scaffold.py

import logging
from pathlib import Path
from typing import Dict, Any, Optional # Keep Dict from typing

from core.giblet_config import giblet_config # Import giblet_config
from . import utils
from .readme_generator import ReadmeGenerator
from .roadmap_generator import RoadmapGenerator
from .style_preference import StylePreferenceManager

class ProjectScaffolder:
    """
    Handles the creation of the local project directory structure and initial files.
    """

    def __init__(self,
                 readme_generator: ReadmeGenerator,
                 roadmap_generator: RoadmapGenerator,
                 style_manager: StylePreferenceManager):
        """
        Initializes the ProjectScaffolder.

        Args:
            readme_generator: An instance of ReadmeGenerator.
            roadmap_generator: An instance of RoadmapGenerator.
            style_manager: An instance of StylePreferenceManager.
        """
        self.readme_generator = readme_generator
        self.roadmap_generator = roadmap_generator
        self.style_manager = style_manager
        self.logger = logging.getLogger(__name__)

    def _create_project_files(self, project_path: Path, project_brief: dict[str, Any]):
        """Creates standard files within the project directory."""
        
        # README
        readme_content, _ = self.readme_generator.generate(project_brief)
        self.style_manager.write_file_with_style(
            filepath=project_path / "README.md",
            content=readme_content, 
            style_category="documentation", # Assuming this is the correct category
        )

        # Roadmap
        roadmap_content = self.roadmap_generator.generate(project_brief)
        self.style_manager.write_file_with_style(
            filepath=project_path / "roadmap.md",
            content=roadmap_content, 
            style_category="documentation",
        )

        # .gitignore
        gitignore_content = "*.pyc\n__pycache__/\n.env\n.venv/\ndata/local_llm_models/\n*.log\n"
        self.style_manager.write_file_with_style(
            filepath=project_path / ".gitignore",
            content=gitignore_content, # Pass the full path
            style_category="configuration", # Or an appropriate category
        )

        # main.py
        main_py_content = f"# main.py for {project_brief.get('title', 'New Project')}\n\n"
        main_py_content += "def main():\n"
        main_py_content += f"    print(\"Welcome to {project_brief.get('title', 'New Project')}!\")\n\n"
        main_py_content += "if __name__ == \"__main__\":\n" # This is the main.py of the new project
        main_py_content += "    main()\n" # It should not import giblet_config from the Giblet's core
        self.style_manager.write_file_with_style(
            filepath=project_path / "main.py",
            content=main_py_content, 
            style_category="source_code",
        )

        # requirements.txt
        requirements_content = "# Project dependencies\nfastapi\nuvicorn\n" # Example content
        self.style_manager.write_file_with_style(
            filepath=project_path / "requirements.txt",
            content=requirements_content, 
            style_category="configuration",
        )
        
        # Create .gitkeep in empty data subdirectories
        utils.write_file(str(project_path / "data" / "prompts" / ".gitkeep"), "")
        utils.write_file(str(project_path / "data" / "documents" / ".gitkeep"), "")
        utils.write_file(str(project_path / "tests" / ".gitkeep"), "")
        utils.write_file(str(project_path / "core" / ".gitkeep"), "")

    def scaffold_local(self,
                       project_name: str,
                       project_brief: Dict[str, Any],
                       base_path: Path = Path.cwd()) -> Optional[Path]:
        """
        Creates the full directory structure and initial files for a new local project.

        Args:
            project_name: The name of the project (e.g., "my-new-app").
            project_brief: The structured brief from the IdeaInterpreter.
            base_path: The base path where the project directory should be created.
                       Defaults to the configured project root.

        Returns:
            The path to the newly created project directory, or None on failure.
        """
        # Sanitize project name for use as a directory name
        project_root_name = utils.sanitize_directory_name(project_name)
        actual_project_path = Path(base_path) / project_root_name
        
        self.logger.info(f"Scaffolding new local project at: {actual_project_path.relative_to(giblet_config.get_project_root())}")

        try:
            # 1. Create root project directory
            actual_project_path.mkdir(parents=True, exist_ok=True)

            # 2. Create standard subdirectories
            # Ensure all necessary directories are created, including nested ones for .gitkeep
            subdirs_to_create = ["core", "data", "tests", "ui", Path("data") / "prompts", Path("data") / "documents"]
            for subdir_name in subdirs_to_create:
                (actual_project_path / subdir_name).mkdir(parents=True, exist_ok=True)
            
            # 3. Create project files
            self._create_project_files(actual_project_path, project_brief)

            self.logger.info(f"Project '{project_name}' scaffolded successfully.")
            return actual_project_path

        except Exception as e:
            import traceback
            self.logger.error(f"❌ Error scaffolding project '{project_name}': {e}\n{traceback.format_exc()}")
            return None
