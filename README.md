# The Giblet: Your Personal AI Development Companion

## 🌟 Vision & Core Philosophy

**The Giblet** is a personalized, evolving, and modular AI Praximate designed to partner with **James** (you!) through every stage of software and creative development. More than just a tool, it's a **personality-aligned, memory-capable, creatively collaborative system** that adapts to your "vibe," translating inspiration into innovation on your terms.

**"Vibe-first. Code-later."**

---

## 🎯 Key Roles & Capabilities

The Giblet functions across five integrated domains, empowering a holistic development experience:

### 🧑‍💻 1. Primary Coder
Transforms prompts into clean, usable, and testable code, acting as an intelligent coding assistant.
* **Code Generation:** Language-aware generation (Python, JS, Rust) from minimal specs, with docstring and typing options.
* **Debugger:** Runs tests, parses tracebacks, suggests/auto-applies fixes, and learns from bug patterns.
* **Unit Tester:** Auto-generates Pytest/unit tests and supports dry-run sessions.
* **Refactor:** Style-agnostic but "James-preferred" refactoring, with auto-generated changelogs and comparisons.
* **Snippets:** Stores and reuses preferred idioms and patterns.

### 🎨 2. Creative Partner
Your dedicated idea bouncer, concept expander, and imaginative wingman.
* **Idea Synthesis:** Brainstorms and evolves code, game, tool, or concept ideas from sketches.
* **Creative Constraints:** Solves problems creatively under defined limitations (e.g., "3D tool in 100 lines").
* **Inspiration Feed:** Curates unique repos, UX, niche projects from GitHub, Reddit, Hacker News, and bookmarks.
* **Weird Mode:** Unleashes experimental and chaotic creative prompts (game jams, cursed UI, ASCII DSLs).

### 📋 3. Project Manager
Organizes development chaos and translates vision into reality through structured cycles.
* **Roadmap Manager:** Generates flexible roadmaps by phase, feature, or vibe, with Markdown export and status updates.
* **Kanban Sync:** Generates JSON/Markdown Kanban boards, exportable to Notion, Trello, GitHub Projects.
* **File Keeper:** Manages file summaries, renames, diffs, and maintains a searchable file map/architecture.
* **Progress Logger:** Auto-logs milestones/commits, generating changelogs, patch notes, and summaries.

### 🧠 4. Learning System
Builds a persistent, personal development "brain" that continuously gets smarter with you.
* **Session Memory:** Short-term memory scoped to the current session/task.
* **Long-Term Memory:** JSON/SQLite powered context log for bugs, refactors, decisions, preferences, and "past James logic."
* **Bug Archive:** Indexed log of bugs, symptoms, fixes, and timestamps.
* **Personal Wiki:** Persistent knowledgebase of tools, gotchas, deployment strategies, and custom utilities.

### 🌀 5. Workflow Assistant: Vibe Coding Engine
Supports deep-focus, immersive development states with minimal disruption, embodying the "Vibe-first" philosophy.
* **Vibe Mode:** Reduces cognitive friction, suggests next steps, manages open files, and maintains rolling context.
* **Checkpoint Recorder:** Snapshots current context (.vibe files) to resume work seamlessly.
* **Background Automator:** Auto-generates TODO lists, stubs for functions, and inline comments.
* **Music Sync (Optional):** BPM-matched progress estimator for subtle workflow cues.

---

## 🧱 Suggested Architecture (High-Level)

```
the_giblet/
├── core/         # Core AI logic (code_gen, debugger, roadmap, memory, vibe_mode)
├── data/         # Persistent storage (changelogs, memory.json, bug_fixes.db)
├── ui/           # User interfaces (cli.py, dashboard.py)
├── tests/        # Test suite
├── main.py       # Main application entry point
└── README.md     # Project documentation
```

---

## 🚀 Milestone v0.1: "Vibehancement"

**Goal:** Create a CLI-based working prototype focusing on **memory and roadmap tracking**.

---

## 💡 Future Expansions

* Visual dashboard (Streamlit, PyQt)
* Git integration + local repo summarizer
* Auto-generated Web UI creation
* Plugin SDK for integration with other AI tools (LangChain, Ollama, Gemini)

---

## 🧠 Philosophy of Use

* Improvise first, structure second.
* Let the AI support the flow, not interrupt it.
* Persist memory, but not rigidity.
* Customize and mutate. This is your brainchild.

---