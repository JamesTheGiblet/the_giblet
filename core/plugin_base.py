# core/plugin_base.py
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    """Abstract base class for all Giblet plugins."""
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    # <<< NEW METHOD
    @abstractmethod
    def register_commands(self, command_manager):
        """Allows the plugin to register its commands."""
        pass