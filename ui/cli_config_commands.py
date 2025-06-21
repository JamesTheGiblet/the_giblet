# ui/cli_config_commands.py
import json
from core.user_profile import UserProfile, DEFAULT_PROFILE_STRUCTURE

def handle_profile_command(args: list[str], user_profile: UserProfile):
    """
    Handles 'profile' subcommands for the CLI.
    """
    if not args:
        print("Usage: profile [get|set|clear] [<category> <key> <value>]")
        print("Current profile data:")
        print(user_profile.get_all_data())
        return

    action = args[0].lower()
    if action == "get":
        if len(args) == 1:
            print(user_profile.get_all_data())
        elif len(args) == 2:
            category_name = args[1]
            category_data = user_profile.data.get(category_name)
            if category_data is not None:
                if category_data:
                    print(f"Preferences in category '{category_name}':")
                    for key, value_item in category_data.items():
                        print(f"  {key}: {value_item}")
                else:
                    print(f"Category '{category_name}' is empty.")
            else:
                print(f"Category '{category_name}' not found.")
        elif len(args) >= 3:
            value = user_profile.get_preference(args[1], args[2])
            print(f"{args[1]}.{args[2]} = {value if value is not None else 'Not set'}")
        else:
            print("Usage: profile get [<category> [<key>]]")
    elif action == "set":
        if len(args) >= 4:
            user_profile.add_preference(args[1], args[2], " ".join(args[3:]))
            print(f"✅ Profile preference '{args[1]}.{args[2]}' set.")
        else:
            print("Usage: profile set <category> <key> <value>")
    elif action == "clear":
        user_profile.clear_profile()
        print("✅ User profile cleared.")
    else:
        print(f"Unknown profile action: {action}. Use 'get', 'set', or 'clear'.")

def handle_llm_config_command(args: list[str], user_profile: UserProfile):
    """
    Handles 'llm' subcommands for the CLI.
    """
    if not args:
        print("Usage: llm <status|use|config> [options...]")
        return

    action = args[0].lower()
    if action == "status":
        active_provider_from_profile = user_profile.get_preference("llm_provider_config", "active_provider")
        effective_active_provider = active_provider_from_profile or "gemini"
        print(f"Effective Active LLM Provider: {effective_active_provider}")
        if not active_provider_from_profile:
            print("  (Note: No active provider explicitly set in profile, defaulting to Gemini)")

        provider_configs = user_profile.get_preference("llm_provider_config", "providers", {})

        for provider_name_key in ["gemini", "ollama"]:
            print(f"\nSettings for {provider_name_key.capitalize()}:")
            config = provider_configs.get(provider_name_key, DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"].get(provider_name_key, {}))
            for key, value in config.items():
                val_display = "*******" if "api_key" in key and value else value
                print(f"  - {key}: {val_display}")
    elif action == "use":
        if len(args) < 2 or args[1].lower() not in ["gemini", "ollama"]:
            print("Usage: llm use <gemini|ollama>")
            return
        provider_name = args[1].lower()
        user_profile.add_preference("llm_provider_config", "active_provider", provider_name)
        print(f"✅ Active LLM provider set to: {provider_name}. Restart Giblet for changes to take full effect in current session.")
    elif action == "config":
        if len(args) < 4:
            print("Usage: llm config <provider_name> <setting_key> <setting_value>")
            return
        provider_name = args[1].lower()
        key = args[2]
        value = " ".join(args[3:])
        user_profile.add_preference(("llm_provider_config", "providers", provider_name), key, value)
        print(f"✅ Set {key} = {value} for {provider_name}. Restart Giblet for changes to take full effect.")
    else:
        print(f"Unknown llm command: {action}. Use 'status', 'use', or 'config'.")