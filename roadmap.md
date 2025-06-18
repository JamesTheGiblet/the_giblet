🧠 **The Giblet: Your Personal AI Dev Companion**

A personalized, evolving, and modular AI Praximate built to partner with James (The Giblet) through every stage of software and creative development — coding, designing, planning, and vibing.

**📌 Core Philosophy**

The Giblet is not just a tool. It's a personality-aligned, memory-capable, creatively collaborative system that adapts to your vibe and helps translate inspiration into innovation — on your terms.

*"Vibe-first. Code-later."*

**🎯 Roles & Capabilities**

🧑‍💻 **1. Primary Coder**
Turns prompts into clean, usable, and testable code.
* **`code_gen`**: Language-aware code generation from minimal specs. Supports modular architecture (e.g., Python, JavaScript, Rust). Includes docstring and typing options.
* **`debugger`**: Runs test files and parses tracebacks. Suggests/auto-applies fixes. Learns from each bug + fix pattern.
* **`unit_tester`**: Autogenerates Pytest/unit tests from code. Supports dry-run test sessions.
* **`refactor`**: Style-agnostic but James-preferred (Giblet-style Python). Auto-generates changelogs and side-by-side comparisons.
* **`snippets`**: Keeps your preferred idioms and patterns as reusable snippets.

🎨 **2. Creative Partner**
Your idea bouncer, concept expander, and imaginative wingman.
* **`idea_synth`**: Brainstorms code, game, tool, or concept ideas. Evolves input sketches into structured features.
* **`creative_constraints`**: Solves problems creatively under defined constraints ("Make a 3D tool in 100 lines.")
* **`inspiration_feed`**: Curates wild repos, weird UX, niche projects, dev tools. Draws from: GitHub, Reddit, Hacker News, and bookmarks.
* **`weird_mode`**: Unleashes chaos: game jam ideas, cursed UI, ASCII DSLs.

📋 **3. Project Manager**
Organizes chaos and translates vision into reality through structured dev cycles.
* **`roadmap_manager`**: Generates roadmap by phase, feature, or vibe. Markdown export with x/🚧/❌ status updates.
* **`kanban_sync`**: Can generate JSON or Markdown Kanban boards. Exports to Notion, Trello, or GitHub Projects.
* **`file_keeper`**: Manages file summaries, renames, diffs. Keeps a searchable file map and architecture.
* **`progress_logger`**: Auto-logs every milestone/code commit. Generates changelogs, patch notes, and summaries.

🧠 **4. Learning System**
Builds up a personal dev brain that gets smarter with you.
* **`session_memory`**: Short-term memory scoped to current session/task.
* **`long_term_memory`**: JSON or SQLite powered context log of bugs, refactors, decisions. Includes: "Past James logic," preference overrules, and preferred syntax.
* **`bug_archive`**: Indexed log of bugs, symptoms, fixes, and timestamps.
* **`personal_wiki`**: Persistent dev knowledgebase of: Tools you’ve used, Known gotchas, Deployment strategies, Custom utilities/snippets.

🌀 **5. Workflow Assistant: Vibe Coding Engine**
Supports deep-focus, immersive dev states with minimal disruption.
* **`vibe_mode`**: Reduces cognitive friction. Suggests next steps, manages open files, and keeps a rolling context.
* **`checkpoint_recorder`**: Snapshot of current context: open files, thoughts, next TODOs. Saveable as `.vibe` files to resume later.
* **`background_automator`**: Auto-generates: TODO lists, stubs for unfinished functions, inline comments.
* **`music_sync`** (optional): BPM-matched progress estimator (e.g., slower tempo == need a break?)

**🧱 Suggested Directory Structure**
```
the_giblet/
├── core/
│   ├── code_gen.py
│   ├── debugger.py
│   ├── roadmap_manager.py
│   ├── memory.py
│   └── vibe_mode.py
│
├── data/
│   ├── changelogs/
│   ├── memory.json
│   └── bug_fixes.db
│
├── ui/
│   ├── cli.py
│   └── dashboard.py
│
├── tests/
│   └── test_all.py
│
├── main.py
└── README.md
```
**🚀 Milestone v0.1: "Vibehancement"**
* **Goal:** Create a CLI-based working prototype with memory and roadmap tracking.
* **Tasks:**
    * Create a basic CLI parser (`argparse`)
    * Implement `session_memory` (in-memory dict)
    * Implement `long_term_memory` (JSON file)
    * Build a simple `roadmap_manager` that can add/view tasks.
    * Connect roadmap to memory (e.g., 'remind me what I was working on').

**🧠 Future Expansions**
* Visual dashboard (Streamlit or PyQt)
* Git integration + local repo summarizer
* Autogen Web UI creator
* Plugin SDK for integrating with other AI tools (LangChain, Ollama, Gemini)

**⚙️ Setup & Use**
```bash
git clone https://github.com/jamesthegiblet/the_giblet
cd the_giblet
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**🧠 Philosophy of Use**
* Improvise first, structure second.
* Let the AI support the flow, not interrupt it.
* Persist memory, but not rigidity.
* Customize and mutate. This is your brainchild.

---
### `roadmap.md`

# 🛠️ The Giblet: Build Roadmap (From Zero to Vibehancement)

*This roadmap reconstructs the path required to build the Giblet prototype as defined — culminating in a modular, CLI-based AI dev partner with memory, planning, and creative abilities.*

---

## Phase 0: 💡 Seed the Vision

**Goal:** Capture the philosophy, roles, goals, and system architecture in written form. This forms the "mind" of the project.
**Success looks like:** We have a completed `README.md` and `roadmap.md` that establish the mission, vibe, roles, and structure of The Giblet.
* [x] **Task 0.1: Define The Giblet’s Philosophy and Vision**
    * Draft `README.md` with roles, philosophy, directory structure, and usage vision.
* [x] **Task 0.2: Draft the Initial Roadmap**
    * Create `roadmap.md` that guides Phase 1–5 development with executable tasks.

---

## Phase 1: ⚙️ Build the Core Skeleton

**Goal:** Construct a simple, testable CLI script that interacts with files and executes commands. This is the minimal working agent.
**Success looks like:** You can run `main.py`, give it an instruction, and it responds with file creation, editing, or execution.
* [x] **Task 1.1: Establish the Workspace**
    * Create the `the_giblet/` project directory and subfolders: `core/`, `data/`, `ui/`, `tests/`.
* [x] **Task 1.2: Create Core Utility Functions**
    * In `core/`, implement and test: `safe_path()`, `read_file()`, `write_file()`, `list_files()`, `execute_command()`.
* [x] **Task 1.3: Build Basic CLI Interface**
    * In `ui/cli.py`, create a prompt system that receives input and routes to modules.
* [x] **Task 1.4: Implement Command Execution**
    * Parse instructions and run them using the core utility functions.

---

## Phase 2: 🧠 Add Memory & Planning Logic

**Goal:** Turn The Giblet into a context-aware system that can plan, remember, and reflect on your actions.
**Success looks like:** The Giblet can recall past decisions, update roadmap tasks, and load/save its session context.
* [x] **Task 2.1: Create `memory.py` Module**
    * Hybrid JSON + SQLite memory model.
    * Implements: `store_memory()`, `load_memory()`, `record_bug()`, `retrieve_context()`.
* [x] **Task 2.2: Implement Roadmap Manager**
    * `core/roadmap_manager.py`: Parses `roadmap.md` and updates task status.
* [x] **Task 2.3: Hook Memory into CLI**
    * Load past context into CLI prompt automatically and allow saving checkpoints.

---

## Phase 3: 🎨 Enable Creative Intelligence

**Goal:** Make The Giblet capable of ideation, brainstorming, and solving problems like a creative partner.
**Success looks like:** When prompted, the system generates multiple solutions, including a "standard" and "weird" version.
* [x] **Task 3.1: Build Creative Prompt Templates**
    * In `core/idea_synth.py`, implement logic for standard and creative/weird solution paths.
* [x] **Task 3.2: Integrate `weird_mode` & `constraints` Options**
    * Enable toggles for constrained idea generation and chaotic brainstorming modes.

---

## Phase 4: 🌀 Add Vibe-Driven Workflow Tools

**Goal:** Give The Giblet the ability to track progress, reduce context-switching, and support deep coding focus.
**Success looks like:** The Giblet can snapshot your work, suggest the next task, and pre-fill stubs.
* [x] **Task 4.1: Implement Vibe Mode Engine**
    * `core/vibe_mode.py`: tracks current focus, last commands, and open files.
* [x] **Task 4.2: Add Checkpoint Recorder**
    * Snapshot context + TODOs to `.vibe` files.
* [x] **Task 4.3: Stub Auto-Generator**
    * Add `background_automator` that parses incomplete functions and adds inline `# TODO:` comments or stubs.

---

## Phase 5: x Integrate Testing & Documentation

**Goal:** Finalize The Giblet into a usable prototype with validation, tests, and modular loading.
**Success looks like:** The entire system is testable with one command and outputs helpful error/debug info.
* [x] **Task 5.1: Add Unit Tests**
    * `tests/test_all.py`: covers each core module.
* [x] **Task 5.2: Add In-CLI Error Handling & Debugging**
    * Graceful crash recovery with traceback logging.
* [x] **Task 5.3: Autogenerate Changelog**
    * Pull commits/changes into a Markdown log.

---
## Phase 6: 🌀 Git-Awareness Engine
* [x] **Task 6.1: Implement Advanced Git Functions**
    * Implemented core Git analysis functions within the `GitAnalyzer` class, enabling status checks, branch listing, and retrieval of commit logs directly from the CLI.
* [x] **Task 6.2: Create AI-Powered Repo Summarizer**
    * Integrated the `IdeaSynthesizer` with `GitAnalyzer` to provide AI-generated summaries of recent repository activity, offering high-level insights into project progress.
* [x] **Task 6.3: Implement Contextual Vibe Mode (Git Branch)**
    * Enhanced the CLI prompt to dynamically display the current Git branch, providing immediate context when a manual focus is not active.

---
## Phase 7: 🎨 The Visual Canvas (Dashboard)
* [x] **Task 7.1: Set Up Basic Streamlit Application**
    * This established the foundational web interface for visualizing project data and interacting with The Giblet's features.
* [x] **Task 7.2: Build Interactive Roadmap Visualization**
    * This created a dynamic view of the `roadmap.md` file, allowing for easy tracking of project phases and task completion within the dashboard.
* [x] **Task 7.3: Create Git History Dashboard Page**
    * This integrated Git analysis to display recent commit history, providing a quick overview of code changes and contributions.
* [x] **Task 7.4: Implement 'Idea Synth' Playground UI**
    * This added an interactive section to the dashboard for leveraging the `IdeaSynthesizer` to brainstorm and explore new concepts.

---
## Phase 8: 🛠️ Proactive Builder Engine
* [x] **Task 8.1: Implement Advanced `code_gen` Module**
    * This enhanced the `CodeGenerator` to produce more robust Python functions and laid the groundwork for more complex code manipulations.
* [x] **Task 8.2: Implement `Autogen Web UI` (Proof of Concept)**
    * This introduced the capability to automatically generate basic Streamlit UIs from Python data class definitions, accessible via the `build ui` CLI command.
* [x] **Task 8.3: Implement `refactor` command**
    * This added a CLI command (`refactor <file> "<instruction>"`) allowing The Giblet to intelligently refactor existing code based on user instructions.

---
## Phase 9: 🔌 The Plugin SDK
* [x] **Task 9.1: Define Plugin Architecture and Entry Points**
    * This established the foundational structure for how plugins are discovered, loaded, and how they register their commands with The Giblet's core system.
* [x] **Task 9.2: Refactor a Core Module into a Plugin**
    * This involved migrating an existing internal component to the new plugin system, serving as a proof-of-concept and ensuring the architecture was practical.
* [x] **Task 9.3: Create Plugin for Local LLMs (Ollama/LangChain)**
    * This demonstrated the extensibility of the plugin system by creating a new plugin to integrate with locally running Large Language Models, expanding The Giblet's capabilities.

---
## Phase 10: 💫 The Sentient Loop (Self-Improvement)
* [x] **Task 10.1: Implement `unit_tester` command**
    * This will introduce a dedicated CLI command for The Giblet to automatically generate comprehensive pytest unit tests for specified Python source files, enhancing code reliability.
* [x] **Task 10.2: Create `test thyself` command**
    * This command will enable The Giblet to autonomously execute its own internal test suite, verifying its operational integrity and the correctness of its modules.
* [x] **Task 10.3: Create `refactor thyself` command (Stretch Goal)**
    * As an advanced capability, this command would allow The Giblet to analyze and refactor its own codebase, aiming for improvements in structure, efficiency, or adherence to preferred coding styles.

## Phase 11: 🤝 The Collaborator (Team Features)
* [x] **Task 11.1: Implement Shared Project State**
    * This laid the groundwork for collaborative features by enabling a shared understanding of project elements, initially focusing on a shared to-do list managed via Redis.
* [x] **Task 11.2: Create Asynchronous Task Assignment Command**
    * Implemented the `todo add "@user" "<description>"` and `todo list` CLI commands, allowing tasks to be assigned and viewed in a shared Redis-backed list.
* [x] **Task 11.3: Develop Shared Team Checkpoints**
    * Enhanced the `checkpoint save` and `checkpoint load` commands to optionally use Redis, allowing teams to share and restore specific Giblet session states.

---
## Phase 12: ☁️ The Deployable Service
* [x] **Task 12.1: Build Core Service API (FastAPI)**
    * This established a robust FastAPI backend, exposing core Giblet functionalities like roadmap viewing and task management through well-defined API endpoints.
* [x] **Task 12.2: Refactor CLI and Dashboard as API Clients**
    * The CLI's `roadmap` command and potentially other features were updated to consume data from the new API, decoupling them from direct core module access. The dashboard would similarly transition to an API-first approach.
* [x] **Task 12.3: Package Giblet Service as a Docker Container**
    * The Giblet backend service was containerized using Docker, simplifying deployment, ensuring consistency across environments, and preparing it for broader accessibility.

---
## Phase 13: 💻 The Environment Integrator (IDE & Shell)
* [x] **Task 13.1: Create VS Code Extension (Proof of Concept)**
    * Develop a basic extension to bring Giblet's commands directly into the VS Code interface.
* [x] **Task 13.2: Implement Shell Alias & Function Wrappers**
    * Create convenient shell aliases and functions to make invoking Giblet features quicker from the terminal.
* [x] **Task 13.3: Build Filesystem Watcher with Proactive Suggestions**
    * Implement a background process that monitors file changes and offers contextual help or automation.

---
## Phase 14: 🤖 The Autonomous Agent
* [x] **Task 14.1: Develop a Task Decomposition Engine**
    * Enable Giblet to break down complex user requests into smaller, manageable sub-tasks.
* [x] **Task 14.2: Implement a Multi-Step Command Execution Loop**
    * Allow Giblet to execute a sequence of commands autonomously to achieve a larger goal.
* [x] **Task 14.3: Add Self-Correction Logic based on Test Failures**
    * Empower Giblet to attempt to fix its own generated code if automated tests fail.

---
## Phase 15: ✨ The Personalization Engine v2.0
* [x] **Task 15.1: Build an Evolving User Profile Model**
    * Create a more sophisticated model of user preferences, coding style, and common patterns.
    * [x] **Task 15.1.1: Design and Implement `UserProfile` Class with Memory Persistence**
        * Created `core/user_profile.py` for storing and managing user-specific data.
    * [x] **Task 15.1.2: Add CLI Commands for Basic Profile Interaction**
        * Implemented `profile get|set|clear` commands in the CLI.
    * [x] **Task 15.1.3: Add Dashboard UI for Profile Management**
        * Created a "Profile" tab in the Streamlit dashboard to view and set preferences.
* [x] **Task 15.2: Implement Dynamic Prompt Personalization**
    * Automatically tailor AI prompts based on the user's profile and current context for more relevant results.
    * [x] **Task 15.2.1: Integrate `UserProfile` into `IdeaSynthesizer` and `CodeGenerator`**
        * Modified core generation modules to accept and use `UserProfile` data.
    * [x] **Task 15.2.2: Add Persona-Based Prompting to `IdeaSynthesizer`**
        * Enhanced `IdeaSynthesizer` to use a `idea_synth_persona` profile setting to influence its response style.
* [🚧] **Task 15.3: Create an Interaction Feedback Loop for Vibe Tuning**
    * Allow users to easily provide feedback on Giblet's suggestions to refine its understanding of their 'vibe'.
    * [x] **Task 15.3.1: Store Last AI Interaction in Memory**
        * Modified `IdeaSynthesizer` and `CodeGenerator` to save a summary of their last output to session memory.
    * [x] **Task 15.3.2: Implement `UserProfile.add_feedback()` Method**
        * Added functionality to `UserProfile` to store timestamped feedback entries (rating, comment, context).
    * [x] **Task 15.3.3: Add `feedback` CLI Command**
        * Created a CLI command for users to rate the last AI output and add comments.
    * [x] **Task 15.3.4: Add Feedback UI to Dashboard**
        * Integrated a section in the dashboard for users to view the last AI interaction and submit feedback (rating/comment).

---
## Phase 16: 🎮 The Interactive Cockpit
* [x] **Task 16.1: Build the 'Generator' Tab**
    * Create a dedicated section in the dashboard for code generation and idea synthesis.
* [x] **Task 16.2: Build the 'Refactor' Tab**
    * Add a UI for selecting files and providing instructions to refactor code.
* [x] **Task 16.3: Build the 'File Explorer' Tab**
    * Implement a file browser within the dashboard to view project files.
* [x] **Task 16.4: Integrate Automation Commands**
    * Add UI elements to trigger automation tasks like changelog generation and TODO stubbing.

## Phase 17: 🧠 The Skillful Agent & Smart Skills Engine
* [🚧] **Task 17.1: Design and Implement the "Skill" Core Framework**
    * Define a system where complex, multi-step operations can be encapsulated as a "skill" that the agent can learn or be programmed with.
    * [x] **Task 17.1.1: Define the Skill Interface/Structure (`core.skill_manager.Skill`)**
        * Created a base `Skill` class with `can_handle`, `get_parameters_needed`, and `execute` methods.
    * [x] **Task 17.1.2: Create a `SkillManager` Class (`core.skill_manager.SkillManager`)**
        * Implemented `SkillManager` to discover, load, and list skills from a `skills/` directory.
    * [🚧] **Task 17.1.3: Implement Basic Skill Validation in `SkillManager`**
        * Add checks for adherence to the `Skill` interface and metadata during discovery.
* [🚧] **Task 17.2: Implement Dynamic Skill Invocation in Agent Planning & Execution**
    * Enhance the agent's `create_plan` method to recognize when a user's high-level goal can be achieved by invoking one or more predefined "skills".
    * [x] **Task 17.2.1: Make Agent `create_plan` Skill-Aware**
        * Updated `Agent.create_plan` to fetch available skills and include them in the LLM prompt.
    * [x] **Task 17.2.2: Update Execution Logic to Handle `skill` Commands**
        * Modified `handle_execute` in CLI to parse and run `skill <SkillName> [params...]` commands.
* [🚧] **Task 17.3: Develop Proactive Skill Creation & Suggestion Mechanism**
    * Implement pattern detection, LLM-powered skill generation, automated testing, and user confirmation for new skills.
    * [x] **Task 17.3.1: Implement CLI Command for User-Initiated Skill Generation from Plan**
        * Added `skills create_from_plan <Name> ["trigger"]` command.
    * [x] **Task 17.3.2: Implement Agent Method to Generate Skill Code via LLM**
        * Created `Agent.generate_skill_from_plan()` to prompt LLM for skill code based on a plan and skill creation guide.
    * [🚧] **Task 17.3.3: Implement Command History Logging**
        * Enhanced `CommandManager` to log executed commands (name, args, timestamp) to persistent memory.
    * [x] **Task 17.3.4: Develop Basic Command History Viewer**
        * Created a CLI command `history commands` to view the logged command history.
    * [x] **Task 17.3.5: Develop Basic Pattern Analyzer for Command History**
        * Implemented `PatternAnalyzer` to find frequent command sequences from the log.
    * [🚧] **Task 17.3.6: Implement Proactive Skill Suggestion based on Pattern Analysis**
        * Enhanced `history analyze_patterns` to allow users to select a detected pattern and generate a skill from it.
        * Added basic proactive suggestion trigger in CLI main loop.

---
## Phase 18: ✨ The Vibe-Centric Visual Cockpit
* [🚧] **Task 18.1: Redesign Dashboard for "Vibe Coding" Principles**
    * Re-evaluate and iterate on the dashboard's UI/UX to minimize friction and align with a more intuitive, "vibe-driven" interaction style.
    * [x] **Task 18.1.1: Implement "Quick Actions & Focus Bar" in Dashboard Sidebar**
        * Added a sidebar to display and manage the current session focus, and for future quick action buttons.
* [🚧] **Task 18.2: Implement Visual Task Decomposition & Planning Interface**
    * Create a dashboard component where users can visually break down high-level goals or see the agent's generated plan in a graphical format.
    * [x] **Task 18.2.1: Enhance Dashboard Plan Display**
        * Updated the "Generated Plan" view in the dashboard to use columns and icons for a more structured and visual representation of plan steps.
* [🚧] **Task 18.3: Introduce Interactive "Vibe Sliders" for AI Behavior**
    * Add UI controls in the dashboard that allow the user to directly influence AI parameters (e.g., creativity, verbosity), linked to the `UserProfile`.
    * [x] **Task 18.3.1: Add UI Controls for IdeaSynthesizer Persona and Creativity**
        * Implemented selectbox for persona and slider for creativity level in the dashboard's Profile tab.
    * [x] **Task 18.3.2: Integrate IdeaSynthesizer Creativity into Prompting**
        * Modified `IdeaSynthesizer` to use the `idea_synth_creativity` profile setting.

---
## Phase 19: 🔑 The Universal LLM Connector
* [x] **Task 19.1: Abstract LLM Provider Interactions**
    * Develop a common interface/wrapper to allow seamless switching between different LLM providers (Gemini, Ollama, etc.).
    * [x] **Task 19.1.1: Define `LLMProvider` Base Class**
        * Created `core/llm_provider_base.py` with an abstract `generate_text` method.
    * [x] **Task 19.1.2: Implement `GeminiProvider` and `OllamaProvider`**
        * Created concrete provider classes for Gemini and Ollama.
    * [x] **Task 19.1.3: Refactor Core Modules to Use `LLMProvider`**
        * Updated `IdeaSynthesizer` and `CodeGenerator` to accept and use an `LLMProvider` instance.
* [x] **Task 19.2: Implement Secure and Flexible API Key Management & Selection**
    * Enhance API key management and allow users to select the active LLM provider/model via CLI and Dashboard, storing this in `UserProfile`.
    * [x] **Task 19.2.1: Update `UserProfile` for LLM Provider Configuration**
        * Added `llm_provider_config` to `UserProfile` to store active provider and specific settings (API keys, models, URLs).
    * [x] **Task 19.2.2: Refactor LLM Instantiation in API, CLI, and Dashboard**
        * Modified core components to dynamically load LLM providers based on `UserProfile` settings.
    * [x] **Task 19.2.3: Add CLI Commands for LLM Configuration**
        * Implemented `llm status|use|config` commands in the CLI.
    * [x] **Task 19.2.4: Add Dashboard UI for LLM Configuration**
        * Added UI elements in the Dashboard's "Profile" tab to manage LLM provider selection and settings.
* [🚧] **Task 19.3: Add "Auto-Recognition" of Model Capabilities (Stretch Goal) via "Capability Gauntlet"**
    * Investigate methods for Giblet to infer capabilities of the selected LLM and adapt its strategies accordingly.
    * [x] **Task 19.3.1: Design the "Capability Gauntlet" System**
        * Defined the concept of a test suite (`data/gauntlet.json`), an `CapabilityAssessor` module, and CLI/UI integration for running tests and viewing a "Capability Profile".
    * [x] **Task 19.3.1: Define Initial Capability Set and Investigation Plan**
        * Outlined potential capabilities (modality, context window, formats, etc.) and methods for recognition (metadata, predefined maps, probing).
    * [x] **Task 19.3.2: Implement `LLMCapabilities` Class and Predefined Map**
        * Created `core/llm_capabilities.py` and `data/model_capabilities.json` to store and retrieve known model capabilities.
    * [x] **Task 19.3.3: Implement `CapabilityAssessor` Module**
        * Developed `core/capability_assessor.py` to load `gauntlet.json` and run programmatic tests (code generation, JSON adherence).
    * [x] **Task 19.3.4: Integrate Gauntlet into CLI and Dashboard**
        * Added `assess model` command to CLI.
        * Added UI in Dashboard's "Profile" tab to run the gauntlet and view results.
        * Added `gauntlet edit` command and UI button to launch `gauntlet_editor.py`.
    * [ ] **Task 19.3.5: Integrate Basic Capability Checks into Core Modules**
        * Begin modifying `IdeaSynthesizer`, `CodeGenerator`, and `Agent` to query `LLMCapabilities` and make simple adjustments (e.g., to `max_tokens` or prompt formatting).
    * [ ] **Task 19.3.6: Research and Implement Provider Metadata Fetching (Gemini, Ollama)**
        * Investigate and add code to `LLMCapabilities` to query provider APIs for model details, if available.
    * [ ] **Task 19.3.7: Store and Utilize Gauntlet-Generated Profiles**
        * Enhance `LLMCapabilities` to load and prioritize gauntlet-generated profiles (e.g., from `UserProfile` or a cache) over predefined maps.
    * [ ] **Task 19.3.8: Expand `gauntlet.json` with More Test Categories and Levels**
        * Add tests for other capabilities like context window limits, instruction following, specific language features, etc.

---
## Phase 20: 📚 The Proactive Knowledge Weaver
* [ ] **Task 20.1: Implement Proactive Learning from User Feedback & Profile**
    * Develop a module to analyze `feedback_log` and `UserProfile` data to automatically suggest or adapt default prompt templates or agent behaviors.
* [ ] **Task 20.2: Build a "Project Contextualizer" Module**
    * Create a system to analyze the current project's structure and recent changes to provide more deeply contextual information to LLMs.
* [ ] **Task 20.3: Introduce "Just-in-Time" Proactive Suggestions in UI/CLI**
    * Enable Giblet to offer unsolicited but relevant suggestions or shortcuts based on the project context and user profile.

---
## Phase 21: 