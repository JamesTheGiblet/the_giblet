import logging
from typing import Dict, Any, Optional

from .llm_provider_base import LLMProvider
from .style_preference import StylePreferenceManager

class RoadmapGenerator:
    """
    Generates a high-level project roadmap based on a project brief.
    """

    def __init__(self, llm_provider: LLMProvider, style_manager: StylePreferenceManager):
        """
        Initializes the RoadmapGenerator.

        Args:
            llm_provider: The language model provider to use for generation.
            style_manager: The manager for retrieving user's style preferences.
        """
        self.llm_provider = llm_provider
        self.style_manager = style_manager
        self.logger = logging.getLogger(__name__)

    def _create_prompt(self, project_brief: Dict[str, Any]) -> str:
        """
        Creates the prompt for the LLM to generate the roadmap.
        """
        style_prefs = self.style_manager.get_all_preferences()
        
        roadmap_format = style_prefs.get("roadmap", {}).get("default_format", "phase_based")
        roadmap_tone = style_prefs.get("roadmap", {}).get("default_tone", "professional")
        
        brief_str = "\n".join([f"- {key}: {value}" for key, value in project_brief.items()])

        prompt = (
            f"You are a project manager tasked with outlining a high-level roadmap for a new software project. "
            f"You must strictly adhere to the user's specified format and style.\n\n"
            f"**User's Style Preferences:**\n"
            f"- Roadmap Format: {roadmap_format}\n"
            f"- Tone: {roadmap_tone}\n\n"
            f"**Project Brief:**\n"
            f"{brief_str}\n\n"
            f"**Your Task:**\n"
            f"Generate a complete `roadmap.md` file. Based on the '{roadmap_format}' format, break the project down into logical phases (e.g., Phase 0: Foundation, Phase 1: Core Features, Phase 2: Deployment). "
            f"Under each phase, list 3-5 specific, actionable tasks as Markdown checkboxes (`- [ ] Task description`).\n"
            f"- The tone of the writing must be consistently '{roadmap_tone}'.\n"
            f"- The output must be a valid Markdown file that our `RoadmapManager` can parse.\n\n"
            f"Output *only* the raw Markdown for the complete `roadmap.md` file. Do not include any other text, comments, or explanations."
        )
        return prompt

    def generate(self, project_brief: Dict[str, Any]) -> str:
        """
        Generates the high-level roadmap content.
        """
        self.logger.info(f"Generating roadmap for project: {project_brief.get('title', 'Untitled Project')}")
        if not self.llm_provider or not self.llm_provider.is_available():
            self.logger.error("Cannot generate roadmap: LLM provider is not available.")
            return "## Roadmap Generation Failed\n\nCould not connect to the LLM provider."
        try:
            prompt = self._create_prompt(project_brief)
            roadmap_content = self.llm_provider.generate_text(
                prompt=prompt,
                max_tokens=1024
            )
            self.logger.info("Successfully generated roadmap content.")
            return roadmap_content
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during roadmap generation: {e}")
            return f"## Roadmap Generation Error\n\nAn unexpected error occurred: {e}"