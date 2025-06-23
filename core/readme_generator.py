# readme_generator.py
import logging
from typing import Dict, Any

from core.llm_provider_base import LLMProvider
from core.style_preference import StylePreferenceManager

class ReadmeGenerator:
    """
    Generates a project README.md file based on a project brief and style preferences.
    """

    def __init__(self, llm_provider: LLMProvider, style_manager: StylePreferenceManager):
        """
        Initializes the ReadmeGenerator.

        Args:
            llm_provider: The language model provider to use for generation.
            style_manager: The manager for retrieving user's style preferences.
        """
        self.llm_provider = llm_provider
        self.style_manager = style_manager
        self.logger = logging.getLogger(__name__)

    def _create_prompt(self, project_brief: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Creates the prompt for the LLM to generate the README.md.
        """
        style_prefs = self.style_manager.get_all_preferences()
        
        # Extract style preferences for the prompt
        readme_style = style_prefs.get("readme", {}).get("default_style", "standard")
        readme_tone = style_prefs.get("readme", {}).get("default_tone", "professional")
        readme_sections = style_prefs.get("readme", {}).get("default_sections", ["Overview", "Features", "Getting Started", "Roadmap Link", "Contributing"])
        
        # Convert the project brief and sections list into a string for the prompt
        # Store the specific preferences used for this generation
        used_style_preferences = {
            "default_style": readme_style,
            "default_tone": readme_tone,
            "default_sections": readme_sections
        }
        brief_str = "\n".join([f"- {key}: {value}" for key, value in project_brief.items()])
        sections_str = ", ".join(readme_sections)

        prompt = (
            f"You are a professional technical writer tasked with creating a README.md file for a new software project. "
            f"You must strictly adhere to the user's specified style and content requirements.\n\n"
            f"**User's Style Preferences:**\n"
            f"- Overall Style: {readme_style}\n"
            f"- Tone: {readme_tone}\n\n"
            f"**Project Brief (Source of Truth):**\n"
            f"{brief_str}\n\n"
            f"**Required Sections:**\n"
            f"You must generate a complete README.md file that includes the following sections in a logical order: {sections_str}.\n"
            f"- Use the 'Project Brief' as the single source of truth for all content.\n"
            f"- The tone of the writing must be consistently '{readme_tone}'.\n"
            f"- The structure should be characteristic of a '{readme_style}' README file.\n"
            f"- If the brief lacks information for a required section, create a sensible placeholder (e.g., 'Installation instructions will be added soon.').\n\n"
            f"Output *only* the raw Markdown for the complete README.md file. Do not include any other text, comments, or explanations before or after the Markdown content."
        )
        return prompt, used_style_preferences # Return both

    def generate(self, project_brief: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
            A tuple: (generated_readme_content_as_string, used_style_preferences_dict).

        Args:
            project_brief: A dictionary containing the structured project brief
                           from the IdeaInterpreter.

        Returns:
            The generated README.md content as a string.
        """
        self.logger.info(f"Generating README for project: {project_brief.get('title', 'Untitled Project')}")
        
        if not self.llm_provider or not self.llm_provider.is_available():
            self.logger.error("Cannot generate README: LLM provider is not available.")
            return "# README Generation Failed\n\nCould not connect to the LLM provider.", {}

        try:
            prompt, used_style_preferences = self._create_prompt(project_brief) # Capture both return values
            
            readme_content = self.llm_provider.generate_text(
                prompt=prompt,
                max_tokens=1024  # Allow for a longer README
            )
            
            self.logger.info("Successfully generated README content.")
            return readme_content, used_style_preferences # Return both

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during README generation: {e}")
            return f"# README Generation Error\n\nAn unexpected error occurred: {e}", {}
