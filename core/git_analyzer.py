# core/git_analyzer.py
import git
from datetime import datetime

class GitAnalyzer:
    def __init__(self):
        """Initializes the Git Analyzer, connecting to the local repository."""
        self.repo = None
        try:
            self.repo = git.Repo(search_parent_directories=True)
            self.git_path = self.repo.git.rev_parse("--show-toplevel")
            print(f"👁️ Git Analyzer connected to repo at: {self.git_path}")
        except git.InvalidGitRepositoryError:
            print("👁️ Git Analyzer: Not a valid Git repository.")
        except Exception as e:
            print(f"❌ An error occurred during Git Analyzer initialization: {e}")

    def get_branch_status(self) -> str:
        """Checks if the repository has uncommitted changes."""
        if not self.repo: return "Not a Git repository."
        
        if self.repo.is_dirty(untracked_files=True):
            return "Uncommitted changes or untracked files present."
        else:
            return "Working directory is clean."

    def list_branches(self) -> list[str]:
        """Lists all local branches in the repository."""
        if not self.repo: return []
        return [branch.name for branch in self.repo.branches]

    def get_commit_log(self, max_count: int = 5) -> list[dict]:
        """Gets the most recent commits from the active branch."""
        if not self.repo: return []
        
        active_branch = self.repo.active_branch
        # <<< FIX: Specify the encoding for reading commit messages
        commits = list(self.repo.iter_commits(active_branch.name, max_count=max_count, encoding='utf-8'))
        
        log = []
        for commit in commits:
            log.append({
                "sha": commit.hexsha[:7],
                "author": commit.author.name,
                "date": datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d'),
                "message": commit.message.strip(),
            })
        return log

    # <<< NEW METHOD
    def summarize_recent_activity(self, idea_synth, max_commits=10) -> str:
        """
        Uses the IdeaSynthesizer to generate a summary of recent commits.
        """
        if not self.repo: return "Not a Git repository."
        if not idea_synth.llm_provider or not idea_synth.llm_provider.is_available(): return "Idea Synthesizer is not available."

        print("🤖 Analyzing commit history for AI summary...")
        commits = self.get_commit_log(max_count=max_commits)
        
        if not commits:
            return "No commits found to summarize."

        # Format the commit log into a simple text block for the AI
        commit_text = "\n".join([
            f"- {c['message']} (by {c['author']} on {c['date']})" for c in commits
        ])

        # Create a specific "meta-prompt" for this task
        summary_prompt = f"""
        Based on the following recent git commit log, please provide a high-level, human-readable summary of the project's progress.
        Focus on the major features completed or bugs fixed. Structure the summary in a few clear bullet points.
        
        **Conclude with a single sentence that reflects the overall momentum or direction of the project.**

        Commit Log:
        {commit_text}
        """

        # <<< CHANGED: Call the new, more direct method
        return idea_synth.generate_text(summary_prompt)