# core/duplication_analyzer.py

import ast
import os
from collections import defaultdict
from pathlib import Path

# --- Core Module Imports ---
# These will be needed for the SemanticAnalyzer
# Note: A placeholder for the actual LLM provider and user profile
# In the final implementation, these would be passed in properly.
from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile

class SyntacticAnalyzer:
    """
    Analyzes Python source code to find structurally duplicate functions
    using Abstract Syntax Trees (AST). This allows it to find code that
    is functionally identical, even if variable names, comments, or
    docstrings are different.
    """
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self._node_hashes = defaultdict(list)

    def _normalize_ast(self, node: ast.AST) -> str:
        class Normalizer(ast.NodeTransformer):
            def visit_Name(self, node):
                return ast.Name(id='_name_', ctx=node.ctx)
            def visit_arg(self, node):
                return ast.arg(arg='_arg_', annotation=None)
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    return ast.Constant(value='_docstring_')
                return node
        return ast.dump(Normalizer().visit(node))

    def analyze_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    body_container = ast.Module(body=node.body)
                    normalized_structure_str = self._normalize_ast(body_container)
                    structure_hash = hash(normalized_structure_str)
                    location_info = {
                        "file": str(file_path.relative_to(self.project_root)),
                        "function_name": node.name,
                        "line_number": node.lineno
                    }
                    self._node_hashes[structure_hash].append(location_info)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError) as e:
            print(f"[SyntacticAnalyzer] Skipping file {file_path}: {e}")

    def find_duplicates(self) -> list[list[dict]]:
        self._node_hashes.clear()
        for root, _, files in os.walk(self.project_root):
            if 'venv' in root or 'site-packages' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    self.analyze_file(Path(root) / file)
        return [locs for locs in self._node_hashes.values() if len(locs) > 1]

class SemanticAnalyzer:
    """
    Analyzes Python source code to find conceptually similar functions
    by creating vector embeddings from their docstrings. This allows it
    to find functions that solve similar problems, even if their code
    structure is different.
    """
    SIMILARITY_THRESHOLD = 0.9 # Configurable threshold for similarity

    def __init__(self, project_root: str | Path, llm_provider: LLMProvider, user_profile: UserProfile):
        self.project_root = Path(project_root)
        self.llm_provider = llm_provider
        self.user_profile = user_profile
        self._function_docs = []

    def _extract_docstrings(self, file_path: Path):
        """Extracts functions and their docstrings from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if docstring: # Only consider functions with docstrings
                        self._function_docs.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "function_name": node.name,
                            "line_number": node.lineno,
                            "docstring": docstring.strip()
                        })
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError) as e:
            print(f"[SemanticAnalyzer] Skipping file {file_path}: {e}")

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Gets embeddings for a list of texts using the LLM provider.
        NOTE: This is a placeholder for the actual implementation.
        """
        if not self.llm_provider:
            print("Warning: No LLM provider configured for SemanticAnalyzer. Skipping.")
            return []
        # In a real scenario, this would make an API call.
        # For now, we simulate it by returning vectors of zeros.
        print(f"Simulating getting embeddings for {len(texts)} docstrings...")
        return [[0.0] * 128 for _ in texts] # Simulate 128-dimensional embeddings

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculates cosine similarity between two vectors."""
        # Placeholder for actual similarity calculation
        import random
        # This will be replaced by a real implementation. For now, it returns
        # random similarities to demonstrate finding different groups.
        return random.uniform(0.8, 1.0) if vec1 and vec2 else 0.0

    def find_duplicates(self) -> list[list[dict]]:
        """Finds conceptually similar functions."""
        self._function_docs.clear()
        for root, _, files in os.walk(self.project_root):
            if 'venv' in root or 'site-packages' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    self._extract_docstrings(Path(root) / file)
        
        if not self._function_docs:
            return []

        docstrings = [f['docstring'] for f in self._function_docs]
        embeddings = self._get_embeddings(docstrings)
        
        if not embeddings:
            return []

        for i, doc_info in enumerate(self._function_docs):
            doc_info['embedding'] = embeddings[i]

        duplicate_groups = []
        processed_indices = set()
        for i in range(len(self._function_docs)):
            if i in processed_indices:
                continue
            
            current_group = [self._function_docs[i]]
            processed_indices.add(i)
            
            for j in range(i + 1, len(self._function_docs)):
                if j in processed_indices:
                    continue
                
                similarity = self._cosine_similarity(
                    self._function_docs[i]['embedding'],
                    self._function_docs[j]['embedding']
                )
                
                if similarity >= self.SIMILARITY_THRESHOLD:
                    current_group.append(self._function_docs[j])
                    processed_indices.add(j)

            if len(current_group) > 1:
                # Clean up the output to match the syntactic analyzer's format
                group_locations = [
                    {k: v for k, v in loc.items() if k != 'embedding'} 
                    for loc in current_group
                ]
                duplicate_groups.append(group_locations)
        
        return duplicate_groups

class DuplicationAnalyzer:
    """
    Orchestrates different types of code analysis to find duplication
    at both a syntactic (structural) and semantic (conceptual) level.
    """
    def __init__(self, project_root: str | Path, llm_provider: LLMProvider = None, user_profile: UserProfile = None):
        self.syntactic_analyzer = SyntacticAnalyzer(project_root)
        self.semantic_analyzer = SemanticAnalyzer(project_root, llm_provider, user_profile)

    def analyze(self) -> dict:
        """
        Runs all configured analyzers and returns a consolidated report.
        """
        print("Starting comprehensive duplication analysis...")
        syntactic_dupes = self.syntactic_analyzer.find_duplicates()
        semantic_dupes = self.semantic_analyzer.find_duplicates()
        print("Analysis complete.")
        
        return {
            "syntactic": syntactic_dupes,
            "semantic": semantic_dupes
        }

if __name__ == '__main__':
    # Example usage:
    # To test, run this file directly from your project's root folder.
    print("Running comprehensive Duplication Analysis...")
    # In a real CLI, the llm_provider and user_profile would be instantiated properly.
    # Here we pass None to show how it gracefully handles the absence.
    analyzer = DuplicationAnalyzer(project_root='.', llm_provider=None, user_profile=None) 
    report = analyzer.analyze()

    # --- Print Syntactic Results ---
    if not report['syntactic']:
        print("\n✅ No STRUCTURALLY duplicate functions found.")
    else:
        print(f"\n🚨 Found {len(report['syntactic'])} group(s) of STRUCTURALLY duplicate functions:")
        for i, group in enumerate(report['syntactic'], 1):
            print(f"\n--- Syntactic Group {i} ---")
            for location in group:
                print(f"  - File: {location['file']}, Function: `{location['function_name']}`, Line: {location['line_number']}")

    # --- Print Semantic Results ---
    if not report['semantic']:
        print("\n✅ No CONCEPTUALLY similar functions found.")
    else:
        print(f"\n🚨 Found {len(report['semantic'])} group(s) of CONCEPTUALLY similar functions:")
        for i, group in enumerate(report['semantic'], 1):
            print(f"\n--- Semantic Group {i} ---")
            for location in group:
                print(f"  - File: {location['file']}, Function: `{location['function_name']}`, Line: {location['line_number']}")
                print(f"    Docstring: \"{location['docstring']}\"")
