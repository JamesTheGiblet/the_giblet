# ui/cli_genesis_flow.py
import json

def run_genesis_interview(initial_idea: str, idea_interpreter, memory_system):
    """
    Handles the common logic for the interactive Q&A session in Genesis mode.

    Args:
        initial_idea (str): The initial idea provided by the user.
        idea_interpreter: An instance of IdeaInterpreter to manage the conversation.
        memory_system: An instance of Memory to store the final brief.
    """
    print(f"\n🚀 Starting Genesis Mode for idea: \"{initial_idea}\"")
    
    questions = idea_interpreter.start_interpretation_session(initial_idea)
    if not questions:
        print("\n❌ Error: Could not start the interpretation session. The LLM might be unavailable.")
        return

    print("\n🤖 The Giblet asks:\n")
    print(questions)
    
    print("\n> Provide your answers below. Type 'EOF' or press Ctrl+D on a new line when you're done.")
    user_answers_lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "EOF":
                break
        except EOFError:
            break
        user_answers_lines.append(line)
    user_answers = "\n".join(user_answers_lines)

    if not user_answers.strip():
        print("\n❌ No answer provided. Aborting Genesis session.")
        return

    print("\nAnalyzing and synthesizing project brief...")
    result = idea_interpreter.submit_answer_and_continue(user_answers)

    if result.get("status") == "complete":
        final_brief = result.get("data", {})
        memory_system.remember("last_genesis_brief", final_brief)
        print("\n--- ✅ Genesis Complete: Synthesized Project Brief ---")
        print(json.dumps(final_brief, indent=2))
        print("----------------------------------------------------\n")
        print("Next step: Run `genesis generate-readme` or `genesis scaffold`.")
    else:
        print(f"\n❌ An error occurred during synthesis: {result.get('message', 'Unknown error.')}")