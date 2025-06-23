# core/idea_interpreter.py
import logging
from typing import Dict, Any, List, Optional

from .llm_provider_base import LLMProvider
from .user_profile import UserProfile
from .memory import Memory
from .readme_generator import ReadmeGenerator # Import new generator
from .roadmap_generator import RoadmapGenerator # Import new generator

from .style_preference import StylePreferenceManager
from .project_contextualizer import ProjectContextualizer
# Removed GenesisLogger import for standard logging

class IdeaInterpreter:
    """
    Manages the conversational chain with the LLM to expand a user's initial idea
    into a structured, actionable project brief.
    """

    def __init__(self,
                 llm_provider: LLMProvider,
                 user_profile: UserProfile,
                 memory: Memory,
                 style_manager: StylePreferenceManager,
                 project_contextualizer: ProjectContextualizer,
                 readme_generator: ReadmeGenerator, # Inject ReadmeGenerator
                 roadmap_generator: RoadmapGenerator): # Inject RoadmapGenerator
        """
        Initializes the IdeaInterpreter.

        Args:
            llm_provider: The language model provider to use for the conversation.
            user_profile: The user's profile to personalize the interaction.
            memory: The memory system for storing conversation state if needed.
            style_manager: The manager for applying the user's preferred style.
            project_contextualizer: Provides context about the current project.
            readme_generator: The ReadmeGenerator instance.
            roadmap_generator: The RoadmapGenerator instance.
        """
        self.llm_provider = llm_provider
        self.user_profile = user_profile
        self.memory = memory
        self.style_manager = style_manager
        self.project_contextualizer = project_contextualizer
        self.logger = logging.getLogger(__name__) # Standard Python logging
        self.conversation_history: List[Dict[str, str]] = []
        self.is_interpreting: bool = False
        self.current_brief: Optional[Dict[str, Any]] = None
        self.readme_generator = readme_generator
        self.roadmap_generator = roadmap_generator
        self.logger.info("Idea Interpreter initialized.")

    def _initial_prompt(self, idea: str) -> str:
        """
        Creates the initial meta-prompt to kick off the interpretation process.
        """
        user_name = self.user_profile.get_preference("general", "user_name", "Dev")
        # Using general_tone from style_preference.json as the communication style
        communication_style = self.style_manager.get_preference("general_tone", "direct and professional")
        project_context_summary = self.project_contextualizer.get_full_context()

        # This is the first "meta-prompt" in the clarification chain.
        # It guides the LLM to ask initial, broad questions.
        prompt = (
            f"You are a 'Genesis Mode' AI, a creative and technical partner. "
            f"Your role is to help me, a developer named {user_name}, "
            f"transform a raw idea into a well-defined project plan. My preferred communication style is '{communication_style}'.\n\n"
            f"Current Project Context (if any):\n{project_context_summary}\n\n"
            f"Here is the initial idea: '{idea}'\n\n"
            f"To help me flesh this out, please ask me 3-4 open-ended questions. These questions should help clarify:\n"
            f"1. The core problem this idea solves or the primary goal it aims to achieve.\n"
            f"2. The key features or functionalities envisioned (1-3 main ones).\n"
            f"3. The intended target audience or users.\n"
            f"4. Any initial thoughts on technology, platform (e.g., web, mobile, CLI), or the project's overall vibe/tone.\n\n"
            f"Please ONLY return the questions, each on a new line. Do not add any conversational fluff before or after the questions."
        )
        return prompt

    def start_interpretation_session(self, initial_idea: str) -> Optional[str]:
        """
        Starts a new idea interpretation session and returns the first set of questions.

        Args:
            initial_idea: The raw idea string from the user.

        Returns:
            The first set of questions from the LLM, or None if an error occurs.
        """
        self.logger.info(f"Starting interpretation for idea: '{initial_idea}'")
        self.conversation_history = []
        self.is_interpreting = True
        self.current_brief = None

        # Start the conversation
        initial_prompt_text = self._initial_prompt(initial_idea)
        # The system prompt itself isn't usually shown to the user, but it guides the first LLM response.
        # We'll add it to history for the LLM's context, but the UI will show the LLM's first questions.
        # self.conversation_history.append({"role": "system", "content": initial_prompt_text}) # For LLM context

        if not self.llm_provider or not self.llm_provider.is_available():
            self.logger.error("LLM provider is not available for idea interpretation.")
            self.is_interpreting = False
            return None

        try:
            self.logger.info("Requesting initial questions from LLM.")
            llm_questions = self.llm_provider.generate_text(prompt=initial_prompt_text, max_tokens=300)
            self.conversation_history.append({"role": "assistant", "content": llm_questions})
            self.logger.info(f"LLM proposed initial questions: {llm_questions}")
            return llm_questions
        except Exception as e:
            self.logger.error(f"Error during LLM call in interpret_idea: {e}")
            self.is_interpreting = False
            return None

    def start_interview(self, initial_idea: str) -> Optional[str]:
        """
        Alias for start_interpretation_session to maintain compatibility with older calls.
        """
        self.logger.warning("Deprecated: 'start_interview' method called. Use 'start_interpretation_session' instead.")
        return self.start_interpretation_session(initial_idea)

    def submit_answer_and_continue(self, user_answer: str) -> Dict[str, Any]:
        """
        Processes the user's answer and decides the next step (more questions or synthesize).

        Args:
            user_answer: The user's response to the last set of questions.

        Returns:
            A dictionary indicating the status:
            - {"status": "error", "message": "..."}
            - {"status": "in_progress", "type": "questions", "data": "New questions..."}
            - {"status": "complete", "type": "brief", "data": {final_brief_dict}}
        """
        if not self.is_interpreting:
            return {"status": "error", "message": "Interpretation session not active or already completed."}

        self.conversation_history.append({"role": "user", "content": user_answer})
        self.logger.info(f"User answered: {user_answer[:100]}...")

        # --- Simplified Logic: Synthesize after the first user answer ---
        # In a real application, you'd have more complex logic here to decide
        # if more questions are needed or if it's time to synthesize.
        # For this example, we'll proceed directly to synthesis after one answer.

        self.logger.info("Proceeding to synthesize brief after one round of Q&A (simplified flow).")
        final_brief_data = self._synthesize_brief()
        if "error" in final_brief_data:
            self.is_interpreting = False # End session on error
            return {"status": "error", "message": final_brief_data["error"]}

        # Generate README and Roadmap after brief is synthesized
        # Capture both the content and the style preferences used for the README
        readme_content, readme_style_used = self.readme_generator.generate(final_brief_data)
        roadmap_content = self.roadmap_generator.generate(final_brief_data)

        # Store generated content in the brief for later access or display
        final_brief_data["generated_readme"] = readme_content
        final_brief_data["generated_readme_style_used"] = readme_style_used # Store the style used
        final_brief_data["generated_roadmap"] = roadmap_content

        # TODO: Integrate ProjectFileManager here to save files to disk

        self.current_brief = final_brief_data
        self.is_interpreting = False
        return {"status": "complete", "type": "brief", "data": final_brief_data}

    def _synthesize_brief(self) -> Dict[str, Any]:
        """
        Synthesizes the conversation history into a structured project brief.
        (Placeholder for now)
        """
        self.logger.info("Synthesizing conversation into final project brief.")
        # In a real implementation, this would involve another LLM call
        # to summarize the conversation_history into a JSON or structured dict.
        # This is the final "meta-prompt" in the clarification chain.
        synthesis_prompt = (
            "Based on the following conversation, synthesize the key information into a structured project brief. "
            "Identify the project title, a one-sentence summary, key objectives (as a list), "
            "a proposed tech stack (as a list), target audience, core features, and the overall project tone/vibe. "
            "If the conversation is too short to determine these, make reasonable placeholders.\n\n"
            "Conversation History:\n"
        )
        for entry in self.conversation_history:
            # Only include assistant and user messages directly in the synthesis prompt body
            # The system prompt (initial instructions) has already guided the conversation.
            if entry['role'] in ['assistant', 'user']:
                synthesis_prompt += f"{entry['role'].capitalize()}: {entry['content']}\n"

        if not self.llm_provider or not self.llm_provider.is_available():
            self.logger.error("LLM provider not available for brief synthesis.")
            return {"error": "LLM provider not available for synthesis."}

        try:
            synthesized_output_str = self.llm_provider.generate_text(prompt=synthesis_prompt, max_tokens=700) # Increased tokens
            # Here, you might want to parse synthesized_output_str if you expect JSON
            # For now, we'll assume it's a text blob that we can put into the brief.
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during brief synthesis: {e}")
            return {"error": f"LLM communication failed during synthesis: {e}"}

        # For this skeleton, we'll return a dummy structure.
        return {
            "title": "Placeholder Project Title",
            "summary": "A brief, one-sentence summary of the project.",
            "objectives": ["Objective 1", "Objective 2"],
            "tech_stack_suggestion": ["python"],
            "target_audience": "General Users",
            "core_features_identified": ["Feature A", "Feature B"],
            "project_vibe_tone": self.style_manager.get_preference("general_tone", "professional"),
            "llm_synthesized_summary": synthesized_output_str, # Store the LLM's direct synthesis
            "conversation_turns": len([msg for msg in self.conversation_history if msg['role'] == 'user'])
        }

    def get_current_conversation_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()

    def get_final_brief(self) -> Optional[Dict[str, Any]]:
        return self.current_brief
