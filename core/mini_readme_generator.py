# core/mini_readme_generator.py

import logging
from pathlib import Path
from typing import Dict, Any

from core.llm_provider_base import LLMProvider
from core.style_preference import StylePreferenceManager
from core.user_profile import UserProfile
from core import utils

class MiniReadmeGenerator:
    """
    Generates and maintains a mini README.md file for a given source file,
    explaining its purpose and components.
    """

    def __init__(self, llm_provider: LLMProvider, style_manager: StylePreferenceManager, user_profile: UserProfile):
        """
        Initializes the MiniReadmeGenerator.

        Args:
            llm_provider: The language model provider.
            style_manager: The manager for applying the user's preferred style.
            user_profile: The user's profile for any personalization.
        """
        self.llm_provider = llm_provider
        self.style_manager = style_manager
        self.user_profile = user_profile
        self.logger = logging.getLogger(__name__)

    def _create_generation_prompt(self, file_content: str, file_path: Path) -> str:
        """
        Creates a specialized prompt for generating a mini README for a code file.
        """
        tone = self.style_manager.get_preference("general_tone", "professional")
        
        prompt = (
            "You are an expert technical writer specializing in creating clear, concise, and developer-friendly documentation. "
            f"Your task is to generate a 'mini README' in Markdown format for the provided code file '{file_path.name}'.\n\n"
            "**Style Guidelines:**\n"
            f"* **Tone:** {tone}\n"
            "* **Format:** Adhere to standard Markdown. Use headers, bullet points, and code blocks for clarity.\n\n"
            "**File Content to Analyze:**\n"
            f"```python\n{file_content}\n```\n\n"
            "**Your Task:**\n"
            "Based on the code above, generate a Markdown document that includes the following sections:\n\n"
            "1.  **`## Purpose`**: A one or two-sentence summary explaining the file's primary role and responsibility within the project.\n"
            "2.  **`## Key Components`**: A bulleted list identifying the main classes, functions, or variables. For each, provide a brief description of what it does.\n"
            "3.  **`## Usage Example`**: If applicable, provide a short, clear code snippet demonstrating how to import and use the key components from this file. If not applicable, state \"No specific usage example required.\"\n\n"
            "Output *only* the raw Markdown for the mini README. Do not include any other text or explanations."
        )
        return prompt

    def _save_readme(self, file_path: Path, readme_content: str) -> bool:
        """
        Saves the generated readme content to a file.
        The readme file will be named [original_filename].readme.md
        """
        readme_path = file_path.with_name(f"{file_path.name}.readme.md")
        self.logger.info(f"Saving mini README for '{file_path.name}' to '{readme_path}'")
        try:
            # Using the project's utility for writing files
            # Note: utils.write_file expects a string path relative to the workspace
            utils.write_file(str(readme_path), readme_content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save mini README to {readme_path}: {e}")
            return False

    def generate_for_file(self, file_path_str: str):
        """
        Reads a file's content, generates a mini README for it, and saves it.
        """
        self.logger.info(f"Starting mini README generation for: {file_path_str}")
        
        # safe_path in utils will handle resolving to the correct project root
        file_path = utils.safe_path(file_path_str)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return

        try:
            content = utils.read_file(file_path_str)
            if not content or not content.strip():
                self.logger.warning(f"File is empty, cannot generate README: {file_path_str}")
                return

            prompt = self._create_generation_prompt(content, file_path)

            readme_content = self.llm_provider.generate_text(prompt=prompt, max_tokens=600)

            if readme_content:
                # The _save_readme expects a Path object
                self._save_readme(file_path, readme_content)
                self.logger.info(f"Successfully generated and saved mini README for {file_path.name}")
            else:
                self.logger.error("LLM failed to generate content for the mini README.")

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during README generation for {file_path_str}: {e}")