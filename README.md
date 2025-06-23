🧠 The Giblet: Your Personal AI Dev Companion

A personalized, evolving, and modular AI The Giblet built to partner with James (The Giblet) through every stage of software and creative development — coding, designing, planning, and vibing.

📌 Core Philosophy and 🧠 Philosophy of Use

    Improvise first, structure second.
    Let the AI support the flow, not interrupt it.
    Persist memory, but not rigidity.
    Customize and mutate. This is your brainchild.

The Giblet is not just a tool. It's a personality-aligned, memory-capable, creatively collaborative system that adapts to your vibe and helps translate inspiration into innovation — on your terms.

"Vibe-first. Code-later."

## Core Features

*   **Code Generation:** Converts prompts into clean, usable, and testable code.
*   **Creative Brainstorming:** Helps generate and expand ideas for code, games, tools, and concepts.
*   **Project Management:** Organizes development cycles and translates vision into reality.
*   **Personalized Learning:** Builds a personal dev brain that learns and adapts to your style.
*   **Workflow Assistance:** Supports deep-focus, immersive development states.

🎯 Roles & Capabilities

🧑‍💻 1. Primary Coder Turns prompts into clean, usable, and testable code.

    code_gen: Language-aware code generation from minimal specs. Supports modular architecture (e.g., Python, JavaScript, Rust). Includes docstring and typing options.
    debugger: Runs test files and parses tracebacks. Suggests/auto-applies fixes. Learns from each bug + fix pattern.
    unit_tester: Autogenerates Pytest/unit tests from code. Supports dry-run test sessions.
    refactor: Style-agnostic but James-preferred (Giblet-style Python). Auto-generates changelogs and side-by-side comparisons.
    snippets: Keeps your preferred idioms and patterns as reusable snippets.

🎨 2. Creative Partner Your idea bouncer, concept expander, and imaginative wingman.

    idea_synth: Brainstorms code, game, tool, or concept ideas. Evolves input sketches into structured features.
    creative_constraints: Solves problems creatively under defined constraints ("Make a 3D tool in 100 lines.")
    inspiration_feed: Curates wild repos, weird UX, niche projects, dev tools. Draws from: GitHub, Reddit, Hacker News, and bookmarks.
    weird_mode: Unleashes chaos: game jam ideas, cursed UI, ASCII DSLs.

📋 3. Project Manager Organizes chaos and translates vision into reality through structured dev cycles.

    roadmap_manager: Generates roadmap by phase, feature, or vibe. Markdown export with x/🚧/❌ status updates.
    kanban_sync: Can generate JSON or Markdown Kanban boards. Exports to Notion, Trello, or GitHub Projects.
    file_keeper: Manages file summaries, renames, diffs. Keeps a searchable file map and architecture.
    progress_logger: Auto-logs every milestone/code commit. Generates changelogs, patch notes, and summaries.

🧠 4. Learning System Builds up a personal dev brain that gets smarter with you.

    session_memory: Short-term memory scoped to current session/task.
    long_term_memory: JSON or SQLite powered context log of bugs, refactors, decisions. Includes: "Past James logic," preference overrules, and preferred syntax.
    bug_archive: Indexed log of bugs, symptoms, fixes, and timestamps.
    personal_wiki: Persistent dev knowledgebase of: Tools you’ve used, Known gotchas, Deployment strategies, Custom utilities/snippets.

🌀 5. Workflow Assistant: Vibe Coding Engine Supports deep-focus, immersive dev states with minimal disruption.

    vibe_mode: Reduces cognitive friction. Suggests next steps, manages open files, and keeps a rolling context.
    checkpoint_recorder: Snapshot of current context: open files, thoughts, next TODOs. Saveable as .vibe files to resume later.
    background_automator: Auto-generates: TODO lists, stubs for unfinished functions, inline comments.
    music_sync (optional): BPM-matched progress estimator (e.g., slower tempo == need a break?)

🚀 Milestone v0.1: "Vibehancement"

    Goal: Create a CLI-based working prototype with memory and roadmap tracking.
    Tasks:
        Create a basic CLI parser (argparse)
        Implement session_memory (in-memory dict)
        Implement long_term_memory (JSON file)
        Build a simple roadmap_manager that can add/view tasks.
        Connect roadmap to memory (e.g., 'remind me what I was working on').

🧠 Future Expansions

    Visual dashboard (Streamlit or PyQt)
    Git integration + local repo summarizer
    Autogen Web UI creator
    Plugin SDK for integrating with other AI tools (LangChain, Ollama, Gemini)

⚙️ Setup & Use

git clone https://github.com/jamesthegiblet/the_giblet
cd the_giblet
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

## Getting Started

To get started with The Giblet, follow these steps:

1.  Clone the repository:

    ```bash
    git clone https://github.com/jamesthegiblet/the_giblet
    ```

2.  Navigate to the project directory:

    ```bash
    cd the_giblet
    ```

3.  Create a virtual environment:

    ```bash
    python -m venv venv
    ```

4.  Activate the virtual environment:

    *   On Windows:

        ```bash
        .\venv\Scripts\activate
        ```

    *   On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```

5.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

6.  Run the Giblet:

    ```bash
    python main.py
    ```

## Roadmap

For details on the project roadmap, see [roadmap.md](roadmap.md).

## Contributing

We welcome contributions! Please refer to the contributing guidelines for more information on how to get involved.

