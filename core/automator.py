# core/automator.py
import ast
from pathlib import Path
import git # <<< NEW IMPORT
from datetime import datetime # <<< NEW IMPORT

class Automator:
    def __init__(self):
        """Initializes the Automator."""
        print("🤖 Automator initialized.")

    def generate_stubs(self, filepath_str: str) -> bool:
        """
        Parses a Python file and adds a TODO comment before the 'pass' statement in empty functions.
        """
        filepath = Path(filepath_str)
        if not filepath.exists() or not filepath.is_file():
            print(f"❌ File not found: {filepath_str}")
            return False

        print(f"🤖 Analyzing {filepath_str} for empty functions...")
        try:
            source_code = filepath.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            
            lines_to_replace = {} # This was lines_to_insert in the previous diff you showed me.
                                  # I'll keep it as lines_to_replace based on the current full file content.
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Case 1: Function with only 'pass'
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        pass_node = node.body[0]
                        line_no = pass_node.lineno
                        # The FIX in your previous request was to insert BEFORE pass.
                        # The current code REPLACES pass.
                        # I will stick to what the current full file shows, which is replacing.
                        lines_to_replace[line_no] = ' ' * pass_node.col_offset + "# TODO: Implement this function."
                    # Case 2: Function with a docstring and then 'pass'
                    elif len(node.body) == 2 and \
                         isinstance(node.body[0], ast.Expr) and \
                         isinstance(node.body[0].value, ast.Str) and \
                         isinstance(node.body[1], ast.Pass):
                        pass_node = node.body[1]
                        line_no = pass_node.lineno
                        lines_to_replace[line_no] = ' ' * pass_node.col_offset + "# TODO: Implement this function."


            if not lines_to_replace:
                print("🤖 No empty functions found to stub.")
                return True

            source_lines = source_code.splitlines()
            
            # This loop replaces the line containing 'pass' with the TODO comment.
            for line_no, new_line in lines_to_replace.items():
                # list index is 0-based, ast line numbers are 1-based
                source_lines[line_no - 1] = new_line
            
            # The previous diff added an extra newline at the end, this version doesn't.
            filepath.write_text('\n'.join(source_lines), encoding='utf-8')
            print(f"✅ Successfully replaced {len(lines_to_replace)} 'pass' statements with TODO stubs.")
            return True

        except Exception as e:
            print(f"❌ An error occurred during stub generation: {e}")
            return False

    # <<< NEW METHOD
    def generate_changelog(self) -> bool:
        """
        Generates a markdown changelog from the project's git history.
        """
        print("🤖 Generating changelog from git history...")
        try:
            repo = git.Repo(search_parent_directories=True)
            changelog_content = ["# Project Changelog\n"]
            
            # <<< FIX: Don't assume the branch name. Get it from the repo directly.
            active_branch = repo.active_branch
            print(f"   (Found active branch: '{active_branch.name}')")
            
            commits = list(repo.iter_commits(active_branch.name, max_count=50))
            for commit in commits:
                commit_time = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')
                line = f"## [{commit.hexsha[:7]}] - {commit_time}\n"
                line += f"**Author:** {commit.author.name}\n\n"
                # Ensure proper markdown blockquote for multi-line messages by prefixing each line
                commit_message_lines = commit.message.strip().splitlines()
                formatted_message = "\n".join([f"> {msg_line}" for msg_line in commit_message_lines])
                line += f"{formatted_message}\n"
                changelog_content.append(line)
            
            changelog_dir = Path(__file__).parent.parent / "data" / "changelogs" # Ensure 'data' directory exists
            changelog_dir.mkdir(parents=True, exist_ok=True) # Create directory if it doesn't exist
            changelog_file = changelog_dir / f"CHANGELOG_{active_branch.name.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md" # Added time and branch to filename
            
            changelog_file.write_text('\n'.join(changelog_content), encoding='utf-8')
            print(f"✅ Changelog saved successfully to {changelog_file}")
            return True
        except git.InvalidGitRepositoryError:
            print("❌ This project is not a valid Git repository, or git is not installed/configured correctly.")
            print("   Please ensure you are in a git project and the 'git' command is accessible in your PATH.")
        except Exception as e:
            print(f"❌ An error occurred during changelog generation: {e}")
            return False
