# ui/dashboard_api_client.py
import httpx
from typing import Any, Dict, List, Optional, Union

class GibletAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)

    def _request(self, method: str, path: str, json: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = 60) -> Dict:
        try:
            response = self.client.request(method, path, json=json, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise Exception(f"API Request Failed for {path}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise Exception(f"API returned error {exc.response.status_code} for {path}: {exc.response.text}") from exc

    # --- Ideas & Genesis ---
    def get_random_weird_idea(self) -> Dict:
        return self._request("POST", "/ideas/random_weird", timeout=60)

    def genesis_start(self, initial_idea: str) -> Dict:
        return self._request("POST", "/genesis/start", json={"initial_idea": initial_idea}, timeout=60)

    def genesis_answer(self, answer: str) -> Dict:
        return self._request("POST", "/genesis/answer", json={"answer": answer}, timeout=120)

    # --- Generation ---
    def generate_readme(self, project_brief: Dict) -> Dict:
        return self._request("POST", "/generate/readme", json={"project_brief": project_brief}, timeout=120)

    def generate_roadmap(self, project_brief: Dict) -> Dict:
        return self._request("POST", "/generate/roadmap", json={"project_brief": project_brief}, timeout=120)

    def refactor_code(self, code_content: str, instruction: str) -> Dict:
        return self._request("POST", "/refactor", json={"code_content": code_content, "instruction": instruction}, timeout=120)

    # --- File Operations ---
    def write_file(self, filepath: str, content: str) -> Dict:
        return self._request("POST", "/file/write", json={"filepath": filepath, "content": content}, timeout=10)

    def list_local_files(self) -> Dict:
        return self._request("GET", "/files/list", timeout=10)

    def read_file(self, filepath: str) -> Dict:
        return self._request("GET", "/file/read", params={"filepath": filepath}, timeout=10)

    # --- Project Management ---
    def scaffold_local_project(self, project_name: str, project_brief: Dict) -> Dict:
        return self._request("POST", "/project/scaffold_local", json={"project_name": project_name, "project_brief": project_brief}, timeout=60)

    def create_github_repo(self, repo_name: str, description: str, private: bool) -> Dict:
        return self._request("POST", "/project/create_github_repo", json={"repo_name": repo_name, "description": description, "private": private}, timeout=60)

    # --- Roadmap ---
    def get_roadmap(self) -> Dict:
        return self._request("GET", "/roadmap", timeout=30)

    # --- Agent ---
    def agent_plan(self, goal: str) -> Dict:
        return self._request("POST", "/agent/plan", json={"goal": goal}, timeout=60)

    def agent_execute(self) -> Dict:
        return self._request("POST", "/agent/execute", timeout=300)

    # --- Automation ---
    def generate_changelog(self) -> Dict:
        return self._request("POST", "/automate/changelog", timeout=30)

    def add_stubs(self, filepath: str) -> Dict:
        return self._request("POST", "/automate/stubs", json={"filepath": filepath}, timeout=30)

    # --- Code Analysis ---
    def analyze_duplicates(self) -> Dict:
        return self._request("POST", "/analyze/duplicates", timeout=120)

    # --- GitHub Integration ---
    def list_github_repo_contents(self, owner: str, repo: str) -> Dict:
        return self._request("POST", "/github/repo/contents", json={"owner": owner, "repo": repo}, timeout=60)

    def get_github_file_content(self, owner: str, repo: str, filepath: str) -> Dict:
        return self._request("POST", "/github/repo/file", json={"owner": owner, "repo": repo, "filepath": filepath}, timeout=30)

    # --- Style Preferences ---
    def set_style_preferences(self, category: str, settings: Dict) -> Dict:
        return self._request("POST", "/style/set_preferences", json={"category": category, "settings": settings}, timeout=10)
