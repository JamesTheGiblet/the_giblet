# plugins/hello_plugin.py
from core.plugin_base import BasePlugin

class HelloPlugin(BasePlugin):
    def get_name(self) -> str:
        return "Hello World Plugin"

    def get_description(self) -> str:
        return "A simple example plugin that says hello."

    def register_commands(self, command_manager):
        command_manager.register("hello", self.say_hello, "Prints a friendly greeting.")

    def say_hello(self, args):
        """The logic for the 'hello' command."""
        print("\n👋 Hello from the plugin system! The Giblet is now extensible.\n")