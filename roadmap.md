🛠️ The Giblet: Build Roadmap (From Zero to Vibehancement)

This roadmap reconstructs the path required to build the Giblet prototype as defined — culminating in a modular, CLI-based AI dev partner with memory, planning, and creative abilities.

Phase 0: 💡 Seed the Vision

Goal: Capture the philosophy, roles, goals, and system architecture in written form. This forms the "mind" of the project. Success looks like: We have a completed README.md and roadmap.md that establish the mission, vibe, roles, and structure of The Giblet.

    [x] * Define The Giblet’s Philosophy and Vision
        * Draft README.md with roles, philosophy, directory structure, and usage vision.
    [x] * Draft the Initial Roadmap
        * Create roadmap.md that guides Phase 1–5 development with executable tasks.
    [x] * Reflect and Evaluate Phase Outcomes
        * Review the initial vision and roadmap structure for clarity and completeness.

Phase 1: ⚙️ Build the Core Skeleton

Goal: Construct a simple, testable CLI script that interacts with files and executes commands. This is the minimal working agent. Success looks like: You can run main.py, give it an instruction, and it responds with file creation, editing, or execution.

    [x] * Establish the Workspace
        * Create the the_giblet/ project directory and subfolders: core/, data/, ui/, tests/.
    [x] * Create Core Utility Functions
        * In core/, implement and test: safe_path(), read_file(), write_file(), list_files(), execute_command().
    [x] * Build Basic CLI Interface
        * In ui/cli.py, create a prompt system that receives input and routes to modules.
    [x] * Implement Command Execution
        * Parse instructions and run them using the core utility functions.
    [x] * Reflect and Evaluate Phase Outcomes
        * Assess the stability and usability of the core CLI and utility functions.

Phase 2: 🧠 Add Memory & Planning Logic

Goal: Turn The Giblet into a context-aware system that can plan, remember, and reflect on your actions. Success looks like: The Giblet can recall past decisions, update roadmap tasks, and load/save its session context.

    [x] * Create memory.py Module
        * Hybrid JSON + SQLite memory model.
        * Implements: store_memory(), load_memory(), record_bug(), retrieve_context().
    [x] * Implement Roadmap Manager
        * core/roadmap_manager.py: Parses roadmap.md and updates task status.
    [x] * Hook Memory into CLI
        * Load past context into CLI prompt automatically and allow saving checkpoints.
    [x] * Reflect and Evaluate Phase Outcomes
        * Verify memory persistence and the roadmap manager's accuracy.

Phase 3: 🎨 Enable Creative Intelligence

Goal: Make The Giblet capable of ideation, brainstorming, and solving problems like a creative partner. Success looks like: When prompted, the system generates multiple solutions, including a "standard" and "weird" version.

    [x] * Build Creative Prompt Templates
        * In core/idea_synth.py, implement logic for standard and creative/weird solution paths.
    [x] * Integrate weird_mode & constraints Options
        * Enable toggles for constrained idea generation and chaotic brainstorming modes.
    [x] * Reflect and Evaluate Phase Outcomes
        * Test the range and quality of creative outputs.

Phase 4: 🌀 Add Vibe-Driven Workflow Tools

Goal: Give The Giblet the ability to track progress, reduce context-switching, and support deep coding focus. Success looks like: The Giblet can snapshot your work, suggest the next task, and pre-fill stubs.

    [x] * Implement Vibe Mode Engine
        * core/vibe_mode.py: tracks current focus, last commands, and open files.
    [x] * Add Checkpoint Recorder
        * Snapshot context + TODOs to .vibe files.
    [x] * Stub Auto-Generator
        * Add background_automator that parses incomplete functions and adds inline # TODO: comments or stubs.
    [x] * Reflect and Evaluate Phase Outcomes
        * Check the effectiveness of vibe mode tools in a typical workflow.

Phase 5: x Integrate Testing & Documentation

Goal: Finalize The Giblet into a usable prototype with validation, tests, and modular loading. Success looks like: The entire system is testable with one command and outputs helpful error/debug info.

    [x] * Add Unit Tests
        * tests/test_all.py: covers each core module.
    [x] * Add In-CLI Error Handling & Debugging
        * Graceful crash recovery with traceback logging.
    [x] * Autogenerate Changelog
        * Pull commits/changes into a Markdown log.
    [x] * Reflect and Evaluate Phase Outcomes
        * Ensure the system is robust and developer-friendly.

Phase 6: 🌀 Git-Awareness Engine

    [x] * Implement Advanced Git Functions
        * Implemented core Git analysis functions within the GitAnalyzer class, enabling status checks, branch listing, and retrieval of commit logs directly from the CLI.
    [x] * Create AI-Powered Repo Summarizer
        * Integrated the IdeaSynthesizer with GitAnalyzer to provide AI-generated summaries of recent repository activity, offering high-level insights into project progress.
    [x] * Implement Contextual Vibe Mode (Git Branch)
        * Enhanced the CLI prompt to dynamically display the current Git branch, providing immediate context when a manual focus is not active.
    [x] * Reflect and Evaluate Phase Outcomes
        * Confirm Git integration provides useful context and summaries.

Phase 7: 🎨 The Visual Canvas (Dashboard)

    [x] * Set Up Basic Streamlit Application
        * This established the foundational web interface for visualizing project data and interacting with The Giblet's features.
    [x] * Build Interactive Roadmap Visualization
        * This created a dynamic view of the roadmap.md file, allowing for easy tracking of project phases and task completion within the dashboard.
    [x] * Create Git History Dashboard Page
        * This integrated Git analysis to display recent commit history, providing a quick overview of code changes and contributions.
    [x] * Implement 'Idea Synth' Playground UI
        * This added an interactive section to the dashboard for leveraging the IdeaSynthesizer to brainstorm and explore new concepts.
    [x] * Reflect and Evaluate Phase Outcomes
        * Gather feedback on dashboard usability and feature completeness.

Phase 8: 🛠️ Proactive Builder Engine

    [x] * Implement Advanced code_gen Module
        * This enhanced the CodeGenerator to produce more robust Python functions and laid the groundwork for more complex code manipulations.
    [x] * Implement Autogen Web UI (Proof of Concept)
        * This introduced the capability to automatically generate basic Streamlit UIs from Python data class definitions, accessible via the build ui CLI command.
    [x] * Implement refactor command
        * This added a CLI command (refactor <file> "<instruction>") allowing The Giblet to intelligently refactor existing code based on user instructions.
    [x] * Reflect and Evaluate Phase Outcomes
        * Test the reliability of code generation and refactoring.

Phase 9: 🔌 The Plugin SDK

    [x] * Define Plugin Architecture and Entry Points
        * This established the foundational structure for how plugins are discovered, loaded, and how they register their commands with The Giblet's core system.
    [x] * Refactor a Core Module into a Plugin
        * This involved migrating an existing internal component to the new plugin system, serving as a proof-of-concept and ensuring the architecture was practical.
    [x] * Create Plugin for Local LLMs (Ollama/LangChain)
        * This demonstrated the extensibility of the plugin system by creating a new plugin to integrate with locally running Large Language Models, expanding The Giblet's capabilities.
    [x] * Reflect and Evaluate Phase Outcomes
        * Ensure the plugin system is stable and easy for others to extend.

Phase 10: 💫 The Sentient Loop (Self-Improvement)

    [ ] * Implement unit_tester command
        * This will introduce a dedicated CLI command for The Giblet to automatically generate comprehensive pytest unit tests for specified Python source files, enhancing code reliability.
    [ ] * Create test thyself command
        * This command will enable The Giblet to autonomously execute its own internal test suite, verifying its operational integrity and the correctness of its modules.
    [ ] * Create refactor thyself command (Stretch Goal)
        * As an advanced capability, this command would allow The Giblet to analyze and refactor its own codebase, aiming for improvements in structure, efficiency, or adherence to preferred coding styles.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Assess the agent's ability to self-test and potentially self-improve.

Phase 11: 🤝 The Collaborator (Team Features)

    [x] * Implement Shared Project State
        * This laid the groundwork for collaborative features by enabling a shared understanding of project elements, initially focusing on a shared to-do list managed via Redis.
    [x] * Create Asynchronous Task Assignment Command
        * Implemented the todo add "@user" "<description>" and todo list CLI commands, allowing tasks to be assigned and viewed in a shared Redis-backed list.
    [x] * Develop Shared Team Checkpoints
        * Enhanced the checkpoint save and checkpoint load commands to optionally use Redis, allowing teams to share and restore specific Giblet session states.
    [x] * Reflect and Evaluate Phase Outcomes
        * Test collaborative features for reliability and ease of use.

Phase 12: ☁️ The Deployable Service

    [x] * Build Core Service API (FastAPI)
        * This established a robust FastAPI backend, exposing core Giblet functionalities like roadmap viewing and task management through well-defined API endpoints.
    [x] * Refactor CLI and Dashboard as API Clients
        * The CLI's roadmap command and potentially other features were updated to consume data from the new API, decoupling them from direct core module access. The dashboard would similarly transition to an API-first approach.
    [x] * Package Giblet Service as a Docker Container
        * The Giblet backend service was containerized using Docker, simplifying deployment, ensuring consistency across environments, and preparing it for broader accessibility.
    [x] * Reflect and Evaluate Phase Outcomes
        * Verify API stability, performance, and ease of deployment.

Phase 13: 💻 The Environment Integrator (IDE & Shell)

    [ ] * Create VS Code Extension (Proof of Concept)
        * Develop a basic extension to bring Giblet's commands directly into the VS Code interface.
    [ ] * Implement Shell Alias & Function Wrappers
        * Create convenient shell aliases and functions to make invoking Giblet features quicker from the terminal.
    [ ] * Build Filesystem Watcher with Proactive Suggestions
        * Implement a background process that monitors file changes and offers contextual help or automation.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Assess how well Giblet integrates into typical developer workflows.

Phase 14: 🤖 The Autonomous Agent

    [ ] * Develop a Task Decomposition Engine
        * Enable Giblet to break down complex user requests into smaller, manageable sub-tasks.
    [ ] * Implement a Multi-Step Command Execution Loop
        * Allow Giblet to execute a sequence of commands autonomously to achieve a larger goal.
    [ ] * Add Self-Correction Logic based on Test Failures
        * Empower Giblet to attempt to fix its own generated code if automated tests fail.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Test the agent's planning, execution, and self-correction capabilities.

Phase 15: ✨ The Personalization Engine v2.0

    [x] * Build an Evolving User Profile Model
        * Create a more sophisticated model of user preferences, coding style, and common patterns.
        * [x] * Design and Implement UserProfile Class with Memory Persistence
            * Created core/user_profile.py for storing and managing user-specific data.
        * [x] * Add CLI Commands for Basic Profile Interaction
            * Implemented profile get|set|clear commands in the CLI.
        * [x] * Add Dashboard UI for Profile Management
            * Created a "Profile" tab in the Streamlit dashboard to view and set preferences.
    [x] * Implement Dynamic Prompt Personalization
        * Automatically tailor AI prompts based on the user's profile and current context for more relevant results.
        * [x] * Integrate UserProfile into IdeaSynthesizer and CodeGenerator
            * Modified core generation modules to accept and use UserProfile data.
        * [x] * Add Persona-Based Prompting to IdeaSynthesizer
            * Enhanced IdeaSynthesizer to use a idea_synth_persona profile setting to influence its response style.
    [🚧] * Create an Interaction Feedback Loop for Vibe Tuning
        * Allow users to easily provide feedback on Giblet's suggestions to refine its understanding of their 'vibe'.
        * [x] * Store Last AI Interaction in Memory
            * Modified IdeaSynthesizer and CodeGenerator to save a summary of their last output to session memory.
        * [x] * Implement UserProfile.add_feedback() Method
            * Added functionality to UserProfile to store timestamped feedback entries (rating, comment, context).
        * [x] * Add feedback CLI Command
            * Created a CLI command for users to rate the last AI output and add comments.
        * [x] * Add Feedback UI to Dashboard
            * Integrated a section in the dashboard for users to view the last AI interaction and submit feedback (rating/comment).
    [ ] * Reflect and Evaluate Phase Outcomes
        * Review how well the personalization features adapt to user preferences and feedback.

Phase 16: 🎮 The Interactive Cockpit

    [x] * Build the 'Generator' Tab
        * Create a dedicated section in the dashboard for code generation and idea synthesis.
    [x] * Build the 'Refactor' Tab
        * Add a UI for selecting files and providing instructions to refactor code.
    [x] * Build the 'File Explorer' Tab
        * Implement a file browser within the dashboard to view project files.
    [x] * Integrate Automation Commands
        * Add UI elements to trigger automation tasks like changelog generation and TODO stubbing.
    [x] * Reflect and Evaluate Phase Outcomes
        * Gather user feedback on the overall dashboard experience and utility.

Phase 17: 🧠 The Skillful Agent & Smart Skills Engine

    [🚧] * Design and Implement the "Skill" Core Framework
        * Define a system where complex, multi-step operations can be encapsulated as a "skill" that the agent can learn or be programmed with.
        * [x] * Define the Skill Interface/Structure (core.skill_manager.Skill)
            * Created a base Skill class with can_handle, get_parameters_needed, and execute methods.
        * [x] * Create a SkillManager Class (core.skill_manager.SkillManager)
            * Implemented SkillManager to discover, load, and list skills from a skills/ directory.
        * [🚧] * Implement Basic Skill Validation in SkillManager
            * Add checks for adherence to the Skill interface and metadata during discovery.
    [🚧] * Implement Dynamic Skill Invocation in Agent Planning & Execution
        * Enhance the agent's create_plan method to recognize when a user's high-level goal can be achieved by invoking one or more predefined "skills".
        * [x] * Make Agent create_plan Skill-Aware
            * Updated Agent.create_plan to fetch available skills and include them in the LLM prompt.
        * [x] * Update Execution Logic to Handle skill Commands
            * Modified handle_execute in CLI to parse and run skill <SkillName> [params...] commands.
    [🚧] * Develop Proactive Skill Creation & Suggestion Mechanism
        * Implement pattern detection, LLM-powered skill generation, automated testing, and user confirmation for new skills.
        * [x] * Implement CLI Command for User-Initiated Skill Generation from Plan
            * Added skills create_from_plan <Name> ["trigger"] command.
        * [x] * Implement Agent Method to Generate Skill Code via LLM
            * Created Agent.generate_skill_from_plan() to prompt LLM for skill code based on a plan and skill creation guide.
        * [🚧] * Implement Command History Logging
            * Enhanced CommandManager to log executed commands (name, args, timestamp) to persistent memory.
        * [x] * Develop Basic Command History Viewer
            * Created a CLI command history commands to view the logged command history.
        * [x] * Develop Basic Pattern Analyzer for Command History
            * Implemented PatternAnalyzer to find frequent command sequences from the log.
        * [🚧] * Implement Proactive Skill Suggestion based on Pattern Analysis
            * Enhanced history analyze_patterns to allow users to select a detected pattern and generate a skill from it.
            * Added basic proactive suggestion trigger in CLI main loop.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Assess the effectiveness of the skill system and proactive suggestions.

Phase 18: ✨ The Vibe-Centric Visual Cockpit

    [🚧] * Redesign Dashboard for "Vibe Coding" Principles
        * Re-evaluate and iterate on the dashboard's UI/UX to minimize friction and align with a more intuitive, "vibe-driven" interaction style.
        * [x] * Implement "Quick Actions & Focus Bar" in Dashboard Sidebar
            * Added a sidebar to display and manage the current session focus, and for future quick action buttons.
    [🚧] * Implement Visual Task Decomposition & Planning Interface
        * Create a dashboard component where users can visually break down high-level goals or see the agent's generated plan in a graphical format.
        * [x] * Enhance Dashboard Plan Display
            * Updated the "Generated Plan" view in the dashboard to use columns and icons for a more structured and visual representation of plan steps.
    [🚧] * Introduce Interactive "Vibe Sliders" for AI Behavior
        * Add UI controls in the dashboard that allow the user to directly influence AI parameters (e.g., creativity, verbosity), linked to the UserProfile.
        * [x] * Add UI Controls for IdeaSynthesizer Persona and Creativity
            * Implemented selectbox for persona and slider for creativity level in the dashboard's Profile tab.
        * [x] * Integrate IdeaSynthesizer Creativity into Prompting
            * Modified IdeaSynthesizer to use the idea_synth_creativity profile setting.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Determine if the "vibe-centric" UI changes improve user experience and focus.

Phase 19: 🔑 The Universal LLM Connector

    [x] * Abstract LLM Provider Interactions
        * Develop a common interface/wrapper to allow seamless switching between different LLM providers (Gemini, Ollama, etc.).
        * [x] * Define LLMProvider Base Class
            * Created core/llm_provider_base.py with an abstract generate_text method.
        * [x] * Implement GeminiProvider and OllamaProvider
            * Created concrete provider classes for Gemini and Ollama.
        * [x] * Refactor Core Modules to Use LLMProvider
            * Updated IdeaSynthesizer and CodeGenerator to accept and use an LLMProvider instance.
    [x] * Implement Secure and Flexible API Key Management & Selection
        * Enhance API key management and allow users to select the active LLM provider/model via CLI and Dashboard, storing this in UserProfile.
        * [x] * Update UserProfile for LLM Provider Configuration
            * Added llm_provider_config to UserProfile to store active provider and specific settings (API keys, models, URLs).
        * [x] * Refactor LLM Instantiation in API, CLI, and Dashboard
            * Modified core components to dynamically load LLM providers based on UserProfile settings.
        * [x] * Add CLI Commands for LLM Configuration
            * Implemented llm status|use|config commands in the CLI.
        * [x] * Add Dashboard UI for LLM Configuration
            * Added UI elements in the Dashboard's "Profile" tab to manage LLM provider selection and settings.
    [🚧] * Add "Auto-Recognition" of Model Capabilities (Stretch Goal) via "Capability Gauntlet"
        * Investigate methods for Giblet to infer capabilities of the selected LLM and adapt its strategies accordingly.
        * [x] * Design the "Capability Gauntlet" System
            * Defined the concept of a test suite (data/gauntlet.json), an CapabilityAssessor module, and CLI/UI integration for running tests and viewing a "Capability Profile".
        * [x] * Define Initial Capability Set and Investigation Plan
            * Outlined potential capabilities (modality, context window, formats, etc.) and methods for recognition (metadata, predefined maps, probing).
        * [x] * Implement LLMCapabilities Class and Predefined Map
            * Created core/llm_capabilities.py and data/model_capabilities.json to store and retrieve known model capabilities.
        * [x] * Implement CapabilityAssessor Module
            * Developed core/capability_assessor.py to load gauntlet.json and run programmatic tests (code generation, JSON adherence).
        * [x] * Integrate Gauntlet into CLI and Dashboard
            * Added assess model command to CLI.
            * Added UI in Dashboard's "Profile" tab to run the gauntlet and view results.
            * Added gauntlet edit command and UI button to launch gauntlet_editor.py.
        * [x] * Integrate Basic Capability Checks into Core Modules
            * Begin modifying IdeaSynthesizer, CodeGenerator, and Agent to query LLMCapabilities and make simple adjustments (e.g., to max_tokens or prompt formatting).
            * Integrated LLMCapabilities into IdeaSynthesizer and CodeGenerator to adjust max_output_tokens for LLM calls.
        * [x] * Research and Implement Provider Metadata Fetching (Gemini, Ollama)
            * Investigate and add code to LLMCapabilities to query provider APIs for model details, if available.
            * Implemented metadata fetching for Gemini (context/output tokens) and Ollama (context tokens).
        * [x] * Store and Utilize Gauntlet-Generated Profiles
            * Enhance LLMCapabilities to load and prioritize gauntlet-generated profiles (e.g., from UserProfile or a cache) over predefined maps.
            * Updated CapabilityAssessor to output determined_capabilities, UserProfile to store/retrieve gauntlet profiles, and LLMCapabilities to load these with high priority. CLI/Dashboard now save gauntlet results.
        * [x] * Expand gauntlet.json with More Test Categories and Levels
            * Add tests for other capabilities like context window limits, instruction following, specific language features, etc.
            * Added context_window_recall and instruction_following test categories to gauntlet.json and updated CapabilityAssessor to handle them.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Ensure LLM provider integration is seamless and capability assessment is accurate.

Phase 20: 📚 The Proactive Knowledge Weaver (Placeholder)

    [🚧] * Implement Proactive Learning from User Feedback & Profile
        * Develop a module to analyze feedback_log and UserProfile data to automatically suggest or adapt default prompt templates or agent behaviors.
        * [x] * Design ProactiveLearner Class and Data Flow in core/proactive_learner.py
            * Defined inputs (UserProfile instance providing feedback log and preferences) and outputs (list of string suggestions).
            * Outlined methods for feedback analysis (analyze_feedback), profile preference analysis (analyze_user_profile_preferences), and suggestion generation (generate_suggestions).
        * [x] * Implement Basic Feedback Analysis Logic in ProactiveLearner
            * Developed analyze_feedback to parse feedback entries, calculate average ratings per context_id, and collect comments.
        * [x] * Implement User Profile Preference Analysis in ProactiveLearner
            * Developed analyze_user_profile_preferences to extract relevant preferences (e.g., ai_verbosity, ai_tone, idea_synth_persona) from UserProfile.
        * [x] * Implement Initial Suggestion Generation Mechanism in ProactiveLearner
            * Created generate_suggestions to formulate actionable string-based suggestions based on combined feedback and profile analysis.
        * [x] * Integrate ProactiveLearner for Suggestion Display (CLI/Dashboard)
            * This will involve adding a CLI command (e.g., giblet learn suggestions) or a dashboard section to trigger the learner and show its suggestions to the user.
            * [x] * Add learn suggestions CLI Command
                * Implemented a new command giblet learn suggestions in ui/cli.py to instantiate ProactiveLearner (using UserProfilePlaceholder for now) and display its suggestions. Added basic error handling and output styling.
            * [x] * Add "Proactive Suggestions" Section to Dashboard
                * Created a new "Proactive Suggestions" tab in ui/dashboard.py with a button to trigger ProactiveLearner (using UserProfilePlaceholder) and display its suggestions. Includes spinner and error/info messages.
        * [x] * Refine context_id Logging for Feedback
            * Ensure that feedback entries consistently log a meaningful context_id (e.g., specific prompt template name, agent task identifier) to improve the specificity and accuracy of proactive learning.
    [🚧] * Build a "Project Contextualizer" Module
        * Create a system to analyze the current project's structure and recent changes to provide more deeply contextual information to LLMs.
        * [x] * Design ProjectContextualizer Class and Core Logic in core/project_contextualizer.py
            * Defined inputs (Memory, GitAnalyzer, project root) and outputs (context string).
            * Outlined methods for file structure analysis, Git history summary, focus retrieval, and context aggregation.
        * [x] * Implement File Structure Analysis in ProjectContextualizer
            * Developed get_file_structure_summary to list relevant project files/directories, with options for filtering and limiting.
        * [x] * Implement Git History Analysis in ProjectContextualizer
            * Implemented get_recent_changes_summary using GitAnalyzer to fetch recent commit messages.
        * [x] * Implement Focus Retrieval in ProjectContextualizer
            * Implemented get_current_focus_summary using Memory to recall the current session focus.
        * [x] * Implement Context Aggregation in ProjectContextualizer
            * Created get_full_context to combine all gathered information into a single string. Added an example usage in if __name__ == '__main__':.
        * [x] * Integrate ProjectContextualizer into Core LLM Interactions
            * Plan and implement how the generated context will be used to augment prompts in IdeaSynthesizer, CodeGenerator, or the Agent's LLM calls.
            * [x] * Update IdeaSynthesizer and CodeGenerator to use ProjectContextualizer
                * Modified __init__ to accept ProjectContextualizer.
                * Updated prompt generation methods to prepend project_contextualizer.get_full_context().
            * [x] * Update Instantiation Points in CLI, API, and Dashboard
                * Created ProjectContextualizer instances in ui/cli.py, api.py, and ui/dashboard.py.
                * Passed these instances to IdeaSynthesizer and CodeGenerator during their initialization.
    [🚧] * Introduce "Just-in-Time" Proactive Suggestions in UI/CLI
        * Enable Giblet to offer unsolicited but relevant suggestions or shortcuts based on the project context and user profile.
        * [x] * Refactor ProactiveLearner to use live UserProfile
            * Modified core/proactive_learner.py to accept core.user_profile.UserProfile instances, allowing it to access real-time profile data.
        * [x] * Implement Basic Just-in-Time Suggestion Display in CLI
            * Updated ui/cli.py to instantiate ProactiveLearner with the live user_profile.
            * Added display_just_in_time_suggestions function, called periodically in the CLI loop.
            * Initially, it shows a suggestion from ProactiveLearner if available and not the default "no suggestions" message.
        * [x] * Enhance Contextuality of CLI Just-in-Time Suggestions
            * Refine display_just_in_time_suggestions to use ProjectContextualizer and last_command_name to offer more targeted advice (e.g., "Noticed you're working on X, consider Y command next").
            * Added specific suggestions for commands like generate function, plan, read <file.py>, write <file.py>, and focus.
        * [x] * Implement Just-in-Time Suggestions in Dashboard (e.g., Toasts)
            * Explore using st.toast or a dismissible st.info box in ui/dashboard.py to show contextual suggestions based on user actions or periodic checks.
            * [x] * Instantiate ProactiveLearner for JIT in Dashboard
                * Created proactive_learner_jit instance in dashboard.py using the live user_profile_instance.
            * [x] * Implement show_jit_toast_suggestion Helper Function
                * Developed a function to generate and display st.toast messages based on action_context and ProactiveLearner/ProjectContextualizer inputs.
            * [x] * Integrate JIT Toasts into Dashboard Actions
                * Added calls to show_jit_toast_suggestion after key actions like code/test generation, profile updates, plan generation, and file viewing.
    [ ] * Reflect and Evaluate Phase Outcomes
        * Review the utility and accuracy of proactive suggestions and contextualization.

Phase 21: 🧠 The Preference & Style Engine (Foundation)

**Goal:** Build the core systems for learning, storing, and managing your personal development "fingerprint."
**Tasks:**
    [x] * Implement `style_preference.py` Module: Create the class and methods for managing the `style_preference.json` file, which will store your preferred formats, tones, and defaults.
    [x] * Implement Genesis Logging: Create the methods to initialize and write to `genesis_log.json`, which will track every project created via this mode.
    [x] * Build "My Vibe" Dashboard UI: Create a new tab in the Cockpit where you can view and manually edit the preferences stored in `style_preference.json`.

    [ ] * Reflect and Evaluate Phase Outcomes
        * Ensure style preferences are correctly applied and easy to manage.

Phase 22: 💬 The Interactive Interpreter

**Goal:** Develop the conversational Q&A system that transforms a simple prompt into a detailed project brief.
**Tasks:**
    [x] * Implement `idea_interpreter.py`: Build the core class that will manage the conversational chain with the LLM.
    [x] * Design the Clarification Prompt Chain: Create the series of "meta-prompts" that guide the LLM to ask intelligent follow-up questions about goals, tech stacks, and tone.
    [x] * Build the "Genesis" UI (Interview Stage): Create the initial UI in a new "Genesis" dashboard tab. It will have a text input for the initial idea and a chat-like interface to display the AI's clarifying questions and capture your answers.

    [ ] * Reflect and Evaluate Phase Outcomes
        * Test the quality of project briefs generated through the interview process.

Phase 23: 📜 The Adaptive Generators

**Goal:** Build the engines that generate the core project documents, making them aware of your learned style preferences.
**Tasks:**
    [x] * Implement Style-Aware README Generation: Enhance the `code_gen` or a new `doc_gen` module to take the project brief and the data from `style_preference.py` to generate a `README.md` that matches your preferred style.
    [x] * Implement Style-Aware Roadmap Generation: Create the `roadmap_generator.py` module. Its primary function will be to use the project brief and style preferences to generate a `roadmap.md` file that is compatible with our existing `RoadmapManager`.
    [x] * Implement the "Reflective Prompts" UI: After a README and roadmap are generated, update the UI to ask the user "Would you like to save this format as your default?" and trigger the update in `style_preference.json`.

    [ ] * Reflect and Evaluate Phase Outcomes
        * Verify that generated documents adhere to style preferences and are useful.

Phase 24: 📂 The Project Scaffolder

**Goal:** Create the functionality to build the actual project workspace, either locally or on GitHub.
**Tasks:**
    [x] * Implement `github_client.py`: Build the module for securely authenticating with the GitHub API (using a GITHUB_TOKEN) and creating new repositories.
    [x] * Implement `project_scaffold.py`: Create the module responsible for creating the local directory structure, including any default files like `.gitignore` or `requirements.txt`.
    [x] * Build the "Workspace Builder" UI: In the Genesis tab, after the documents are approved, present the user with the choice ("Local Folder" or "Create GitHub Repo") and use the appropriate backend module to execute their choice.

    [ ] * Reflect and Evaluate Phase Outcomes
        * Ensure project scaffolding works reliably for both local and GitHub projects.

Phase 25: 🎲 The Final Vibe

**Goal:** Implement the final features that complete the Genesis experience and link it back to the coding workflow.
**Tasks:**
    [x] * Implement "Random Genesis" Mode: Add a "🎲 Surprise Me" button to the Genesis UI that uses the `IdeaSynthesizer` to generate a random, weird project concept and feeds it into the Genesis pipeline.
    [x] * Implement `vibe_engine.py` (Post-Genesis): Create the initial version of this engine. After a project is scaffolded, it will proactively suggest the first logical `giblet` command (e.g., "Project created. Would you like to focus on the first task in the roadmap?").

Phase 26: 🧪 The Experimental Playground

**Goal:** Explore and integrate advanced, experimental features that enhance creativity, maintain project coherence, and support spontaneous workflow improvements.

**Tasks:**
    [x] * Implement Duplicate Code Detection
    * * Develop a module that scans the codebase for duplicate or highly similar code blocks.
    * * Integrate with the CLI and dashboard to highlight potential duplications and suggest refactoring opportunities.
    * * Optionally, provide automated refactoring or snippet extraction for repeated patterns.

    [x] * Add "Vibe Button" for Spontaneous Updates
    * * Create a UI element ("Vibe Button") in the dashboard and CLI that allows users to instantly capture new ideas or changes as they arise.
    * * When pressed, prompt the user for a quick note or idea, then automatically update the `README.md` and `roadmap.md` with the new information or tasks.
    * * Maintain a log of vibe-driven changes for future review and refinement.

    [x] * Develop a Sanity Checker for Project Alignment
    * * Build a "sanity checker" module that periodically reviews the codebase, `README.md`, and `roadmap.md` for alignment.
    * * Detect and flag discrepancies between documented plans and actual implementation (e.g., missing features, outdated docs).
    * * Provide actionable suggestions to bring the project back in sync with its stated goals and roadmap.

    [x] * Implement Proactive Modularity Guardrails
    * * Objective: To prevent code centralization and encourage modular design by monitoring file length and suggesting intelligent refactoring opportunities.

Phase 27: Reflect and Evaluate Phase Outcomes, Reflect and Evaluate Phase Outcomes**

    [ ] * Assess the value and usability of experimental features.
    [ ] * Review the overall Genesis Mode experience and its integration with the core workflow.
    [ ] * async setup
    [ ] * MERN setup
