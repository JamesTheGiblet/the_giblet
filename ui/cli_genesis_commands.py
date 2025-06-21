# ui/cli_genesis_commands.py
import httpx
from pathlib import Path

from core import utils
from core.memory import Memory
from core.idea_interpreter import IdeaInterpreter
from core.readme_generator import ReadmeGenerator
from core.roadmap_generator import RoadmapGenerator
from core.genesis_logger import GenesisLogger
from core.style_preference import StylePreferenceManager
from ui.cli_genesis_flow import run_genesis_interview

def handle_genesis(
    args: list[str],
    idea_interpreter_cli: IdeaInterpreter,
    memory: Memory,
    readme_generator_cli: ReadmeGenerator,
    roadmap_generator_cli: RoadmapGenerator,
    genesis_logger_cli: GenesisLogger,
    style_manager_for_cli: StylePreferenceManager
):
    """
    Handles all 'genesis' subcommands for the CLI.
    """
    valid_subcommands = ["start", "generate-readme", "generate-roadmap", "scaffold", "publish", "random", "log"]
    if not args or args[0].lower() not in valid_subcommands:
        print("Usage: genesis <subcommand> [options...]")
        print(f"Valid subcommands: {', '.join(valid_subcommands)}")
        return
    
    subcommand = args[0].lower()
    if subcommand == "start":
        if len(args) < 2:
            print("Usage: genesis start \"<your initial project idea>\"")
            return
        initial_idea = " ".join(args[1:])
        run_genesis_interview(initial_idea, idea_interpreter_cli, memory)
    
    elif subcommand == "random":
        print("🎲 Summoning a strange and wonderful new project idea...")
        try:
            response = httpx.post("http://localhost:8000/ideas/random_weird", timeout=60)
            response.raise_for_status()
            data = response.json()
            random_idea = data.get("idea")
            if random_idea:
                run_genesis_interview(random_idea, idea_interpreter_cli, memory)
            else:
                print("❌ The API did not return a random idea.")
        except Exception as e:
            print(f"❌ Failed to get a random idea from the API: {e}")

    elif subcommand == "generate-readme":
        print("\nGenerating Project README...")
        last_brief = memory.recall("last_genesis_brief")
        if not isinstance(last_brief, dict) or not last_brief:
            print("❌ No project brief found. Please run `genesis start` first.")
            return
        
        readme_content = readme_generator_cli.generate(last_brief)
        print("\n--- Generated README.md ---\n" + readme_content + "\n---------------------------\n")
        save_file_confirm = input("Save this content to README.md? (y/n): ").lower()
        if save_file_confirm == 'y':
            if utils.write_file("README.md", readme_content):
                print("✅ README.md saved successfully!")
            else:
                print("❌ Failed to save README.md.")
        else:
            print("Save to file cancelled.")

    elif subcommand == "generate-roadmap":
        print("\nGenerating Project Roadmap...")
        last_brief = memory.recall("last_genesis_brief")
        if not isinstance(last_brief, dict) or not last_brief:
            print("❌ No project brief found. Please run `genesis start` first.")
            return
        
        roadmap_content = roadmap_generator_cli.generate(last_brief)
        print("\n--- Generated roadmap.md ---\n" + roadmap_content + "\n----------------------------\n")
        
        save_confirm = input("Save this content to roadmap.md? (y/n): ").lower()
        if save_confirm == 'y':
            if utils.write_file("roadmap.md", roadmap_content):
                print("✅ roadmap.md saved successfully!")
            else:
                print("❌ Failed to save roadmap.md.")
        else:
            print("Save cancelled.")

    elif subcommand == "scaffold":
        print("\n🏗️ Scaffolding local project...")
        last_brief = memory.recall("last_genesis_brief")
        if not isinstance(last_brief, dict) or not last_brief:
            print("❌ No project brief found. Please run `genesis start` first.")
            return

        project_name = last_brief.get("title", "new_giblet_project")
        payload = {"project_name": project_name, "project_brief": last_brief}

        try:
            response = httpx.post("http://localhost:8000/project/scaffold_local", json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            print(f"✅ {data.get('message', 'Local project scaffolded successfully.')}")
            if data.get('path'):
                print(f"   Project path: {data.get('path')}")
        except httpx.RequestError:
            print("❌ API Request Failed: Could not connect to Giblet API.")
        except httpx.HTTPStatusError as e:
            print(f"❌ API returned error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

    elif subcommand == "publish":
        print("\n☁️ Creating GitHub repository...")
        last_brief = memory.recall("last_genesis_brief")
        if not isinstance(last_brief, dict) or not last_brief:
            print("❌ No project brief found. Please run `genesis start` first.")
            return

        repo_name = last_brief.get("title", "new-giblet-project").lower().replace(" ", "-")
        description = last_brief.get("summary", "A new project generated by The Giblet.")
        payload = {"repo_name": repo_name, "description": description, "private": True}

        try:
            response = httpx.post("http://localhost:8000/project/create_github_repo", json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            print(f"✅ {data.get('message', 'GitHub repository created successfully.')}")
        except Exception as e:
            print(f"❌ Failed to create GitHub repository: {e}")

    elif subcommand == "log":
        if len(args) < 3:
            print("Usage: genesis log <project_name> \"<initial_brief>\"")
            return
        project_name_arg = args[1]
        initial_brief_arg = " ".join(args[2:])
        placeholder_settings = {
            "readme_style": style_manager_for_cli.get_preference("readme.default_style", "standard"),
            "roadmap_format": style_manager_for_cli.get_preference("roadmap.default_format", "phase_based"),
            "tone": style_manager_for_cli.get_preference("general_tone", "neutral")
        }
        genesis_logger_cli.log_project_creation(
            project_name=project_name_arg,
            initial_brief=initial_brief_arg,
            genesis_settings_used=placeholder_settings,
        )