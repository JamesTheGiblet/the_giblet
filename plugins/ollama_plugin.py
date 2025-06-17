# plugins/ollama_plugin.py
from core.plugin_base import BasePlugin
try:
    from langchain_community.chat_models import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class OllamaPlugin(BasePlugin):
    def __init__(self):
        self.llm = None
        if OLLAMA_AVAILABLE:
            try:
                # This assumes Ollama is running and has the 'llama3' model
                self.llm = ChatOllama(model="llama3")
                print("🦙 Ollama plugin initialized with model 'llama3'.")
            except Exception as e:
                print(f"🦙 Ollama plugin loaded, but failed to connect to Ollama service: {e}")
        else:
            print("🦙 Ollama plugin loaded, but langchain/ollama dependencies are missing.")

    def get_name(self) -> str:
        return "Ollama Local LLM"

    def get_description(self) -> str:
        return "Provides commands to interact with a locally running Ollama LLM."

    def register_commands(self, command_manager):
        if self.llm:
            command_manager.register("local_idea", self.get_local_idea, "Brainstorms an idea using the local Ollama LLM.")

    def get_local_idea(self, args):
        """The logic for the 'local_idea' command."""
        if not args:
            print("Usage: local_idea \"<your prompt>\"")
            return

        prompt = " ".join(args)
        print(f"🦙 Sending prompt to local LLM: '{prompt}'...")

        try:
            with open("data/giblet_debug.log", "a") as f:
                f.write(f"\n--- Ollama Prompt ---\n{prompt}\n")

            response = self.llm.invoke(prompt)

            print("\n--- Local LLM Response ---")
            print(response.content)
            print("--------------------------\n")
        except Exception as e:
            print(f"❌ An error occurred while communicating with Ollama: {e}")