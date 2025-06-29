# core/github_client.py

import os
import httpx
import logging, base64
from typing import Optional, Dict, Any

class GitHubClient:
    """
    A client for interacting with the GitHub API.
    Handles repository creation and other GitHub-related tasks.
    """
    API_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """
        Initializes the GitHubClient.

        Args:
            token: A GitHub Personal Access Token (PAT). If not provided,
                   it will be read from the GITHUB_TOKEN environment variable.
        """
        self.logger = logging.getLogger(__name__)
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            self.logger.warning("GITHUB_TOKEN environment variable not set. GitHub operations will fail.")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_repo(self, repo_name: str, description: str, private: bool = True) -> Dict[str, Any]:
        """
        Creates a new repository on GitHub for the authenticated user.

        Args:
            repo_name: The name of the repository (e.g., "my-new-project").
            description: A short description for the repository.
            private: Whether the repository should be private. Defaults to True.

        Returns:
            A dictionary containing the API response from GitHub on success.
            If an error occurs, it returns a dictionary with an 'error' key.
        """
        if not self.token:
            return {"error": "GitHub token not configured. Please set the GITHUB_TOKEN environment variable."}

        endpoint = f"{self.API_URL}/user/repos"
        payload = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": True,  # Creates the repo with an initial commit and a README
        }

        self.logger.info(f"Attempting to create GitHub repository: {repo_name}")
        try:
            with httpx.Client() as client:
                response = client.post(endpoint, headers=self.headers, json=payload, timeout=20.0)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                
            data = response.json()
            self.logger.info(f"Successfully created repository '{repo_name}'. URL: {data.get('html_url')}")
            return data
        
        except httpx.HTTPStatusError as e:
            error_details = {}
            try:
                error_details = e.response.json()
            except Exception:
                error_details = {"message": e.response.text or "Unknown HTTP error."}

            message = error_details.get("message", "An unknown error occurred.")
            errors = error_details.get("errors", [])
            if errors and isinstance(errors, list) and len(errors) > 0 and 'message' in errors[0]:
                message += f" Details: {errors[0].get('message')}"
            
            self.logger.error(f"GitHub API error when creating repo '{repo_name}': {message}")
            return {"error": message, "status_code": e.response.status_code}
        
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during GitHub repo creation: {e}")
            return {"error": str(e)}

    def list_repo_contents(self, owner: str, repo: str, path: str = "") -> list[str] | dict:
        """
        Lists all files in a GitHub repository recursively.
        """
        if not self.token:
            return {"error": "GitHub token not configured."}

        all_files = []
        
        def get_contents(current_path):
            endpoint = f"{self.API_URL}/repos/{owner}/{repo}/contents/{current_path}"
            try:
                with httpx.Client() as client:
                    response = client.get(endpoint, headers=self.headers, timeout=20.0)
                    response.raise_for_status()
                
                items = response.json()
                for item in items:
                    if item['type'] == 'file':
                        all_files.append(item['path'])
                    elif item['type'] == 'dir':
                        get_contents(item['path']) # Recurse into subdirectory
            except httpx.HTTPStatusError as e:
                # This will be caught by the outer try-except
                raise e
        
        try:
            get_contents(path)
            return sorted(all_files)
        except httpx.HTTPStatusError as e:
            error_details = e.response.json()
            message = error_details.get("message", "An unknown error occurred.")
            self.logger.error(f"GitHub API error listing contents for '{owner}/{repo}': {message}")
            return {"error": message, "status_code": e.response.status_code}
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during GitHub repo content listing: {e}")
            return {"error": str(e)}

    def get_file_content(self, owner: str, repo: str, filepath: str) -> dict[str, Any]:
        """Retrieves the content of a specific file from a GitHub repository."""
        if not self.token:
            return {"error": "GitHub token not configured."}

        endpoint = f"{self.API_URL}/repos/{owner}/{repo}/contents/{filepath}"
        self.logger.info(f"Fetching file content from GitHub: {owner}/{repo}/{filepath}")
        try:
            with httpx.Client() as client:
                response = client.get(endpoint, headers=self.headers, timeout=20.0)
                response.raise_for_status()
            
            data = response.json()
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode('utf-8')
                return {"filepath": filepath, "content": content}
            else:
                return {"error": "File content is not base64 encoded or encoding is missing."}
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during GitHub file content retrieval: {e}")
            return {"error": str(e)}
