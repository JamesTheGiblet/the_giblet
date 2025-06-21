# 🚀 The Giblet – Genesis Mode (v2)  
*Project Creation Reimagined: Adaptive, Reflective, Vibe-Driven*

## 🧠 What Is Genesis Mode?

**Genesis Mode** is The Giblet’s creative forge — a powerful, adaptive pipeline that transforms a single idea into a living, memory-aware software project. It interprets your vibe, scaffolds the plan, generates documentation, builds a repo or workspace, and prepares everything for real-time, creative coding.

It's not a wizard. It's not a tool.  
It's the **origin ritual** of your next idea.

---

## 🧪 Features

### 🌱 Idea Interpreter
- Natural language prompt expands into a full project brief
- Asks follow-up questions to clarify goals, tone, or technology
- Supports Random Genesis: surprise yourself with a weird, AI-generated concept

### 📜 README Generator
- Builds a custom-tailored `README.md` from your brief
- Auto-learns your style, length, tone, and structure from past projects
- Editable inside the UI before confirmation

### 🧭 Roadmap Generator
- Breaks the idea into *Phases → Tasks → Milestones*
- Supports multiple formats (3-phase, waterfall, bullet-based, Kanban-friendly)
- Fully trackable inside the cockpit UI

### 📂 Workspace Builder
- Choose local folder or connect to GitHub
- Create public or private repos
- Initializes structure, pre-stubs, and logs

### 🧠 Preference Engine
- Learns your:
  - Preferred tone
  - Roadmap formatting
  - Repo visibility default
  - Coding language or framework tendencies
- Adapts future projects accordingly

### 🔄 Reflective Prompts
- After project setup, The Giblet asks if you'd like to:
  - Store this format for future use
  - Set as default structure
  - Remember README/roadmap style
- Logged into `style_preference.json` and `genesis_log.json`

---

## 🛠️ Technical Modules (For Builders)

- `idea_interpreter.py`: LLM-powered Q&A → Project Brief
- `roadmap_generator.py`: Context-aware breakdown of phases/tasks
- `style_preference.py`: Manages your build “fingerprint”
- `github_client.py`: Secure repo creation and pushes
- `project_scaffold.py`: Folder/repo setup
- `vibe_engine.py`: Post-gen coding suggestions and auto-tasks
- `genesis_log.json`: Tracks every project you’ve sparked

---

## 🌀 Example Genesis Flow

1. “I want to build an app that lets plants text their owners when thirsty.”
2. Giblet expands this into a brief, asks about sensors/platform/etc.
3. README + roadmap generated. You confirm or edit.
4. You choose to start locally or via GitHub.
5. Files are created, project initialized, context saved.
6. You dive into vibe-mode: coding, planning, experimenting — with The Giblet guiding, learning, and evolving.

---

## 🎲 Bonus: Random Genesis

Try "🎲 Surprise Me" to let The Giblet invent a weird, experimental project for you. Great for jams, rapid prototyping, and escaping creative ruts.

---

## 🌌 Genesis History

All sessions stored in:
- `genesis_log.json`: Project metadata, behavior, entropy level
- `style_preference.json`: Your default structure, formatting, and vibes
- Can be queried later to replicate ideas, formats, or entire setups

---

## 💡 Why It Matters

Genesis Mode empowers *anyone* — developer, artist, tinkerer — to turn sparks into sustainable, trackable, evolvable work.  
No blank files. No lost flow. Just your idea, growing — with memory.

---