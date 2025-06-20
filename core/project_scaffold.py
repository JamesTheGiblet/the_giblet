# core/project_scaffold.py

import logging
from pathlib import Path
from typing import Dict, Any, Optional # Keep Dict from typing

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

    def _create_project_files(self, project_path: Path, project_brief: dict[str, Any], base_path_for_files: Path):
        """Creates standard files within the project directory."""
        
        # README
        readme_content = self.readme_generator.generate(project_brief)
        self.style_manager.write_file_with_style(
            filepath=base_path_for_files / "README.md", # Pass the full path to the style manager
            content=readme_content, 
            style_category="documentation", # Assuming this is the correct category
            project_root=base_path_for_files
        )

        # Roadmap
        roadmap_content = self.roadmap_generator.generate(project_brief)
        self.style_manager.write_file_with_style(
            filepath=base_path_for_files / "roadmap.md", # Pass the full path
            content=roadmap_content, 
            style_category="documentation",
            project_root=base_path_for_files
        )

        # .gitignore
        gitignore_content = "*.pyc\n__pycache__/\n.env\n.venv/\ndata/local_llm_models/\n*.log\n"
        self.style_manager.write_file_with_style(
            filepath=base_path_for_files / ".gitignore",
            content=gitignore_content, # Pass the full path
            style_category="configuration", # Or an appropriate category
            project_root=base_path_for_files
        )

        # main.py
        main_py_content = f"# main.py for {project_brief.get('title', 'New Project')}\n\n"
        main_py_content += "def main():\n"
        main_py_content += f"    print(\"Welcome to {project_brief.get('title', 'New Project')}!\")\n\n"
        main_py_content += "if __name__ == \"__main__\":\n"
        main_py_content += "    main()\n"
        self.style_manager.write_file_with_style( # Pass the full path
            filepath=base_path_for_files / "main.py",
            content=main_py_content, 
            style_category="source_code",
            project_root=base_path_for_files
        )

        # requirements.txt
        requirements_content = "# Project dependencies\nfastapi\nuvicorn\n" # Example content
        self.style_manager.write_file_with_style(
            filepath=base_path_for_files / "requirements.txt", # Pass the full path
            content=requirements_content, 
            style_category="configuration",
            project_root=base_path_for_files
        )
        
        # Create .gitkeep in empty data subdirectories
        utils.write_file(base_path_for_files / "data" / "prompts" / ".gitkeep", "", project_root=base_path_for_files)
        utils.write_file(base_path_for_files / "data" / "documents" / ".gitkeep", "", project_root=base_path_for_files)
        utils.write_file(base_path_for_files / "tests" / ".gitkeep", "", project_root=base_path_for_files)
        utils.write_file(base_path_for_files / "core" / ".gitkeep", "", project_root=base_path_for_files)

    def scaffold_local(self,
                       project_name: str,
                       project_brief: Dict[str, Any],
                       base_path: Path = Path.cwd()) -> Optional[Path]:
        """
        Creates the full directory structure and initial files for a new local project.

        Args:
            project_name: The name of the project (e.g., "my-new-app").
            project_brief: The structured brief from the IdeaInterpreter.
            base_path: The parent directory where the project folder will be created.
                       Defaults to the current working directory.

        Returns:
            The path to the newly created project directory, or None on failure.
        """
        # Sanitize project name for use as a directory name
        project_root_name = utils.sanitize_directory_name(project_name)
        actual_project_path = base_path / project_root_name
        
        self.logger.info(f"Scaffolding new local project at: {actual_project_path}")

        try:
            # 1. Create root project directory
            actual_project_path.mkdir(parents=True, exist_ok=True)

            # 2. Create standard subdirectories
            # Ensure all necessary directories are created, including nested ones for .gitkeep
            subdirs_to_create = ["core", "data", "tests", "ui", Path("data") / "prompts", Path("data") / "documents"]
            for subdir_name in subdirs_to_create:
                (actual_project_path / subdir_name).mkdir(parents=True, exist_ok=True)
            
            # 3. Create project files using the new method
            self._create_project_files(actual_project_path, project_brief, base_path_for_files=actual_project_path)

            self.logger.info(f"Project '{project_name}' scaffolded successfully.")
            return actual_project_path

        except Exception as e:
            import traceback
            self.logger.error(f"❌ Error scaffolding project '{project_name}': {e}\n{traceback.format_exc()}")
            return None
