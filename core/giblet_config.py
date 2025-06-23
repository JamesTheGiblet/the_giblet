import os

class GibletConfig:
    _instance = None
    _project_root = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GibletConfig, cls).__new__(cls)
        return cls._instance

    def set_project_root(self, path: str):
        # Validate path exists and is a directory
        if not os.path.isdir(path):
            raise ValueError(f"Provided project root path is not a valid directory: {path}")
        self._project_root = os.path.abspath(path)
        print(f"Giblet project root set to: {self._project_root}")

    def get_project_root(self) -> str:
        if self._project_root is None:
            # Default to the directory where the `the_giblet` package is located.
            self._project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
            print(f"Defaulting Giblet project root to: {self._project_root}")
        return self._project_root

    def get_file_path(self, relative_path: str) -> str:
        """Constructs an absolute path for a file relative to the project root."""
        return os.path.join(self.get_project_root(), relative_path)

giblet_config = GibletConfig()