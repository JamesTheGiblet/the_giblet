# core/project_contextualizer.py
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.giblet_config import giblet_config # Import giblet_config
from .git_analyzer import GitAnalyzer
from .memory import Memory
from . import utils # Assuming utils.py is in the same directory (core)

class ProjectContextualizer:
    """
    Analyzes the current project's structure, recent changes, and focus
    to provide contextual information for LLMs.
    """

    def __init__(self, memory_system: Memory, project_root: str = "."):
        """Initializes the ProjectContextualizer.

        Args:
            memory_system: An instance of the Memory system to recall focus.
            project_root: The root directory of the project to analyze.
                          Defaults to the globally configured project root.
        """
        self.memory = memory_system
        self.project_root = Path(project_root).resolve()
        self.git_analyzer = GitAnalyzer()

    def get_file_structure_summary(self, max_files: int = 20, ignore_dirs: List[str] = None, relevant_extensions: List[str] = None) -> str:
        """
        Provides a summary of the project's file structure.

        Args:
            max_files: Maximum number of files to list to keep the summary concise.
            ignore_dirs: List of directory names to ignore (e.g., ['.git', '__pycache__', 'venv']).
            relevant_extensions: List of file extensions to prioritize (e.g., ['.py', '.md', '.json']).

        Returns:
            A string summarizing the file structure.
        """
        if ignore_dirs is None:
            ignore_dirs = ['.git', '.idea', '.vscode', '__pycache__', 'venv', 'node_modules', 'build', 'dist', 'data/memory_long_term.json']
        if relevant_extensions is None:
            relevant_extensions = ['.py', '.md', '.txt', '.json', '.yml', '.yaml', '.toml', 'Dockerfile', '.sh', '.ipynb']

        files_list = []
        for item in self.project_root.rglob('*'):
            if any(part in ignore_dirs for part in item.parts):
                continue
            if item.is_file():
                if relevant_extensions and item.suffix.lower() not in relevant_extensions and item.name not in relevant_extensions : # check full name for files like Dockerfile
                    continue
                relative_path = item.relative_to(self.project_root)
                files_list.append(str(relative_path))
        
        files_list.sort()
        summary = "Project File Structure (Partial):\n"
        if not files_list:
            return summary + "  - No relevant files found or project empty.\n"
            
        for f_path in files_list[:max_files]:
            summary += f"  - {f_path}\n"
        
        if len(files_list) > max_files:
            summary += f"  ... and {len(files_list) - max_files} more files.\n"
        return summary

    def get_recent_changes_summary(self, num_commits: int = 3) -> str:
        """
        Provides a summary of recent Git commits.

        Args:
            num_commits: Number of recent commits to summarize.

        Returns:
            A string summarizing recent Git activity.
        """
        if not self.git_analyzer.repo:
            return "Recent Changes: Not a Git repository or no commits found.\n"
        
        commits = self.git_analyzer.get_commit_log(max_count=num_commits)
        summary = f"Recent Changes (last {len(commits)} commits):\n"
        if not commits:
            return summary + "  - No recent commits.\n"
            
        for commit in commits:
            summary += f"  - {commit.get('sha', 'N/A')[:7]}: {commit.get('message', 'No message').strip()}\n" # Display only short SHA
        return summary

    def get_current_focus_summary(self) -> str:
        """
        Retrieves the current focus from memory.

        Returns:
            A string indicating the current focus.
        """
        focus = self.memory.recall("current_focus")
        if focus and not isinstance(focus, str) or (isinstance(focus, str) and not focus.startswith("I don't have a memory for")):
            return f"Current Focus: {str(focus)}\n"
        return "Current Focus: Not set.\n"

    def get_full_context(self) -> str:
        """
        Combines all contextual information into a single string.
        """
        context_parts = []
        context_parts.append(self.get_file_structure_summary())
        context_parts.append(self.get_recent_changes_summary())
        context_parts.append(self.get_current_focus_summary())
        return "\n".join(context_parts)

if __name__ == '__main__':
    # Example Usage (assuming this script is run from the project root or a subdirectory)
    # For this to work, memory.py needs to be runnable standalone or Memory needs a file path
    # For simplicity, we'll assume a basic Memory() can be instantiated.
    
    # Adjust path to go up one level if this file is in core/
    project_root_path = Path(__file__).parent.parent 
    
    mem = Memory() # Memory now uses giblet_config internally
    mem.remember("current_focus", "Refactoring the API authentication module.")
    
    contextualizer = ProjectContextualizer(memory_system=mem, project_root=str(project_root_path))
    full_context = contextualizer.get_full_context()
    print("--- Project Context ---")
    print(full_context)

    print("\n--- File Structure Details ---")
    print(contextualizer.get_file_structure_summary(max_files=5, relevant_extensions=['.py']))

    print("\n--- Recent Changes Details ---")
    print(contextualizer.get_recent_changes_summary(num_commits=2))