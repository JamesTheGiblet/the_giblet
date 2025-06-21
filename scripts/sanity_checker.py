# core/sanity_checker.py

import git
import re
from pathlib import Path
from typing import List, Dict, Any
from core.memory import Memory
# Assuming these will be passed in, similar to other modules.
from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile


class SanityChecker:
    """
    Analyzes the project state to ensure alignment between documentation
    (like the roadmap) and the actual codebase.
    """

    def __init__(self, project_root: str | Path, llm_provider: LLMProvider, user_profile: UserProfile):
        """
        Initializes the Sanity Checker.

        Args:
            project_root: The root directory of the project.
            llm_provider: The language model provider for semantic analysis.
            user_profile: The user's profile for configuration.
        """
        self.project_root = Path(project_root)
        self.llm_provider = llm_provider
        self.user_profile = user_profile
        try:
            self.repo = git.Repo(self.project_root, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            self.repo = None
            print("⚠️ Sanity Checker: Not a Git repository. Sanity checks on commit will be disabled.")

    def _get_completed_tasks_from_roadmap(self) -> List[str]:
        """
        Parses the roadmap.md file and returns a list of tasks
        that are marked as complete.
        """
        roadmap_path = self.project_root / "roadmap.md"
        completed_tasks = []
        if not roadmap_path.exists():
            return []

        # Regex to find completed markdown tasks: `[x]` or `[X]`
        task_pattern = re.compile(r"-\s*\[[xX]\]\s+(.*)")
        with open(roadmap_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = task_pattern.match(line.strip())
                if match:
                    completed_tasks.append(match.group(1).strip())
        return completed_tasks

    def _get_staged_code_changes(self) -> Dict[str, str]:
        """
        Gets the content of staged Python files from the Git index.

        Returns:
            A dictionary mapping file paths to their staged content.
        """
        if not self.repo:
            return {}

        staged_files_content = {}
        # Use diff('HEAD') to get changes that are staged but not yet committed.
        for diff_item in self.repo.index.diff('HEAD'):
            # We are interested in new files (A) and modified files (M)
            if diff_item.change_type in ('A', 'M') and diff_item.a_path.endswith('.py'):
                try:
                    # diff_item.a_blob corresponds to the version in the index (staged)
                    if diff_item.a_blob:
                         staged_content = diff_item.a_blob.data_stream.read().decode('utf-8')
                         staged_files_content[diff_item.a_path] = staged_content
                except Exception as e:
                    print(f"Could not read staged file {diff_item.a_path}: {e}")

        return staged_files_content
    
    async def _summarize_code_chunk(self, code: str) -> str:
        """
        Uses the LLM to generate a one-sentence summary of a code block.
        NOTE: Placeholder for the actual LLM call.
        """
        if not self.llm_provider:
            return "No LLM provider available to summarize code."
        
        # In a real implementation, this would be a more sophisticated prompt
        prompt = f"Summarize the following Python code's purpose in a single, concise sentence:\n\n```python\n{code}\n```"
        
        # Simulate an LLM call
        # summary = await self.llm_provider.generate_text(prompt)
        # return summary
        
        return f"A function or class related to: {code.splitlines()[0]}" # Simplified placeholder

    async def run_pre_commit_check(self) -> List[str]:
        """
        Runs the sanity check designed for a pre-commit hook.

        Returns:
            A list of discrepancy messages. An empty list means no issues found.
        """
        if not self.repo:
            return ["Sanity check skipped: Not a Git repository."]

        completed_tasks = self._get_completed_tasks_from_roadmap()
        staged_changes = self._get_staged_code_changes()

        if not completed_tasks:
            # If no tasks are marked as complete, there's nothing to check.
            return []

        if not staged_changes:
            # If tasks are complete but no .py files are staged, that's a discrepancy.
            return [
                f"Task '{task}' is marked complete, but no Python code is staged for this commit."
                for task in completed_tasks
            ]
            
        # --- This is where the "Proof-of-Work" analysis would happen ---
        # For now, we will use a simplified placeholder logic.
        # A real implementation would use vector embeddings as we designed.
        
        print("[Sanity Check] Analyzing staged code against completed tasks...")
        
        discrepancies = []
        task_accounted_for = {task: False for task in completed_tasks}

        # Simplified check: does any part of the task description appear in the staged code?
        for task in completed_tasks:
            task_keywords = set(re.findall(r'\b\w+\b', task.lower()))
            found_match = False
            for filepath, content in staged_changes.items():
                content_lower = content.lower()
                # If a significant portion of keywords match, consider it accounted for.
                if len(task_keywords.intersection(re.findall(r'\b\w+\b', content_lower))) > 1:
                    task_accounted_for[task] = True
                    found_match = True
                    break
            if not found_match:
                 discrepancies.append(f"Task '{task}' is marked complete, but no strongly corresponding code was found in the staged files.")

        return discrepancies


if __name__ == '__main__':
    # Example Usage (requires a Git repository to function fully)
    print("Running Sanity Checker example...")
    
    # This example assumes it's run from the root of a git project.
    # We create a dummy LLM provider for the test.
    class DummyLLM(LLMProvider):
        async def generate_text(self, prompt: str, **kwargs) -> str:
            return "A dummy summary."

    checker = SanityChecker(project_root='.', llm_provider=DummyLLM(), user_profile=UserProfile(memory_system=Memory()))
    
    print("\n1. Checking for completed tasks in roadmap.md...")
    tasks = checker._get_completed_tasks_from_roadmap()
    if tasks:
        print(f"Found completed tasks: {tasks}")
    else:
        print("No completed tasks found in roadmap.md.")

    print("\n2. Checking for staged Python files...")
    staged = checker._get_staged_code_changes()
    if staged:
        print(f"Found {len(staged)} staged .py files: {list(staged.keys())}")
    else:
        print("No staged .py files found.")

    print("\n3. Running pre-commit check simulation...")
    import asyncio
    discrepancies = asyncio.run(checker.run_pre_commit_check())

    if not discrepancies:
        print("\n✅ Sanity check simulation passed with no issues.")
    else:
        print("\n🚨 Sanity check simulation found the following discrepancies:")
        for issue in discrepancies:
            print(f"  - {issue}")
