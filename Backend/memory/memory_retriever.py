from memory.conversation_memory import get_recent_history


def retrieve_memory(query, last_n=3):
    """
    Retrieve recent conversation history relevant to the current query.
    Currently returns the last N conversation turns.
    """

    history = get_recent_history(last_n)

    if not history:
        return "No previous conversation."

    memory = []

    for turn in history:

        memory.append(f"User: {turn['user']}")
        memory.append(f"Assistant: {turn['assistant']}")
        memory.append("")

    return "\n".join(memory)
