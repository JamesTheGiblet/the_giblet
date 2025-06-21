# core/plugin_manager.py
import importlib
from pathlib import Path
from core.plugin_base import BasePlugin

class PluginManager:
    def __init__(self, plugin_folder="plugins"):
        self.plugin_folder = Path(plugin_folder)
        self.plugins = []
        print("🔌 Plugin Manager initialized.")

    def discover_plugins(self):
        """Discovers and loads all valid plugins from the plugin folder."""
        print(f"🔌 Discovering plugins in '{self.plugin_folder}'...")
        if not self.plugin_folder.is_dir():
            print("   Plugin folder not found.")
            return

        for file in self.plugin_folder.glob("*.py"):
            if file.name.startswith("__"):
                continue

            module_name = f"{self.plugin_folder.name}.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type) and issubclass(attribute, BasePlugin) and attribute is not BasePlugin:
                        # Found a plugin class, instantiate it
                        plugin_instance = attribute()
                        self.plugins.append(plugin_instance)
                        print(f"   ✅ Loaded plugin: '{plugin_instance.get_name()}'")
            except Exception as e:
                print(f"   ❌ Failed to load plugin from {file.name}: {e}")