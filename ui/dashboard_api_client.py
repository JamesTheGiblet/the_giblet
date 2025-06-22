# ui/dashboard_api_client.py
# ui/dashboard_api_client.py

from typing import Dict, List, Optional
import httpx

class GibletAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def _request(self, method: str, endpoint: str, **kwargs):
        try:
            response = self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            # Handle connection errors, timeouts, etc.
            raise Exception(f"API request failed: Could not connect to {e.request.url}.") from e
        except httpx.HTTPStatusError as e:
            # Handle 4xx/5xx responses
            raise Exception(f"API returned an error: {e.response.status_code} - {e.response.text}") from e
        except Exception as e:
            # Handle other potential errors like JSON decoding
            raise Exception(f"An unexpected error occurred in API client: {e}") from e

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

    # ---   Profile   ---
    def get_user_profile(self) -> Dict:
        """Fetches the user profile data from the /profile endpoint."""
        return self._request("GET", "/profile")