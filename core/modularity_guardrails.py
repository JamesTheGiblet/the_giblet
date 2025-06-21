import os

class ModularityGuardrails:
    """
    Implements proactive modularity guardrails by monitoring file length
    and suggesting refactoring opportunities.
    """
    def __init__(self, config=None):
        self.config = config if config else {}
        # Default to 500 lines, can be overridden by config or CLI arg
        self.default_length_threshold = self.config.get('file_length_threshold', 500)

    def _count_lines(self, file_path):
        """Counts the number of lines in a given file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return 0

    def check_file_length(self, file_path, threshold=None):
        """
        Checks if a file exceeds a given line length threshold.
        Returns (bool, int) -> (exceeds_threshold, line_count)
        """
        current_threshold = threshold if threshold is not None else self.default_length_threshold
        line_count = self._count_lines(file_path)
        return line_count > current_threshold, line_count

    def scan_project(self, root_dir, file_extensions=None, length_threshold=None):
        """
        Scans the project directory for files exceeding the length threshold.
        Returns a list of (file_path, line_count) for files exceeding the threshold.
        """
        if file_extensions is None:
            file_extensions = ['.py'] # Default to Python files

        long_files = []
        current_length_threshold = length_threshold if length_threshold is not None else self.default_length_threshold

        print(f"Scanning project for files longer than {current_length_threshold} lines...")

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(dirpath, filename)
                    exceeds, line_count = self.check_file_length(file_path, current_length_threshold)
                    if exceeds:
                        long_files.append((file_path, line_count))
                        print(f"  Found long file: {file_path} ({line_count} lines)")
        return long_files

    def suggest_refactoring(self, long_files_report):
        """
        Generates refactoring suggestions based on the long files report.
        """
        suggestions = []
        if not long_files_report:
            suggestions.append("No files exceeded the length threshold. Your project seems modular!")
        else:
            suggestions.append("The following files are quite long and might benefit from refactoring to improve modularity:")
            for file_path, line_count in long_files_report:
                suggestions.append(f"- {file_path} ({line_count} lines)")
                suggestions.append(f"  Suggestion: Consider breaking down large functions or classes within '{os.path.basename(file_path)}' into smaller, more focused modules or components. This improves readability, testability, and reusability.")
        return "\n".join(suggestions)