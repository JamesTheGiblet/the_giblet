# core/pattern_analyzer.py
from collections import Counter

class PatternAnalyzer:
    def __init__(self, memory_system):
        self.memory = memory_system
        self.COMMAND_LOG_KEY = "giblet_command_log_v1" # Should match CommandManager
        print("🔬 Pattern Analyzer initialized.")

    def find_frequent_sequences(self, command_log: list[dict], min_len: int = 2, max_len: int = 4, min_occurrences: int = 2) -> list[tuple[tuple[str, ...], int]]:
        """
        Finds frequently occurring sequences of commands.
        A command is represented by its name. Args are ignored for this basic version.
        """
        if not command_log:
            return []

        # Extract just the command names
        command_names = [entry.get("command", "") for entry in command_log if entry.get("command")]

        sequences = Counter()

        for n in range(min_len, max_len + 1):
            for i in range(len(command_names) - n + 1):
                sequence = tuple(command_names[i:i+n])
                sequences[sequence] += 1
        
        # Filter by minimum occurrences
        frequent_sequences = [(seq, count) for seq, count in sequences.items() if count >= min_occurrences]
        
        # Sort by count (descending) and then by sequence length (descending)
        frequent_sequences.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        
        return frequent_sequences

    def analyze_command_history(self, min_len: int = 2, max_len: int = 4, min_occurrences: int = 2):
        """
        Retrieves command log and analyzes it for frequent sequences.
        """
        command_log = self.memory.retrieve(self.COMMAND_LOG_KEY)
        if not isinstance(command_log, list) or not command_log:
            print("No command history found to analyze.")
            return []

        print(f"\n🔬 Analyzing command history for frequent sequences (min_len={min_len}, max_len={max_len}, min_occurrences={min_occurrences})...")
        frequent_patterns = self.find_frequent_sequences(command_log, min_len, max_len, min_occurrences)

        if not frequent_patterns:
            print("No significant command patterns detected with current settings.")
            return []
        
        return frequent_patterns