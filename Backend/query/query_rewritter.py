import re

def rewrite_query(query, conversation_history, constraints):
    """
    Rewrite conversational queries into clean, non-duplicated retrieval queries.
    Handles fusion, ingredient addition, and restriction queries seamlessly while preserving conversation context.
    """
    query = query.lower().strip()
    avoided = constraints.get("ingredients_to_avoid", [])
    clean_avoid = list(dict.fromkeys([a.lower().strip() for a in avoided if a and len(a) > 1]))

    history_queries = []
    if conversation_history:
        for line in conversation_history.split("\n"):
            if line.startswith("User:"):
                history_queries.append(line.replace("User:", "").strip().lower())

    # Find primary dish from history
    base_dish = ""
    if history_queries:
        for h in reversed(history_queries):
            # Clean up query filler words to find dish name
            clean_h = re.sub(r"\b(give|generate|recipe|for|me|how|to|make|prepare|i|want|need|a|an|the|without|with)\b", "", h).strip()
            if clean_h and len(clean_h) > 2:
                base_dish = clean_h
                break

    # Extract addition phrases like "add X", "also X", "include X", "with X"
    add_match = re.search(r"\b(?:add|also add|include|put|with|plus)\s+([a-zA-Z ,]+)", query)
    addition_terms = []
    if add_match:
        raw_add = add_match.group(1).strip()
        stop_words = {"in", "it", "to", "recipe", "dish", "please", "some", "the", "that"}
        tokens = [t.strip() for t in re.split(r"[,\s\+]+", raw_add) if t.strip()]
        addition_terms = [t for t in tokens if len(t) > 2 and t not in stop_words and t not in clean_avoid]

    retrieval_parts = []

    if base_dish:
        retrieval_parts.append(base_dish)

    if addition_terms:
        retrieval_parts.append("with")
        retrieval_parts.extend(addition_terms)
    elif not base_dish:
        # Standard query construction if no history base dish
        if constraints.get("protein") == "high":
            retrieval_parts.append("high protein")
        if constraints.get("meal"):
            retrieval_parts.append(constraints["meal"])
        if constraints.get("diet"):
            retrieval_parts.append(constraints["diet"])

        words = [w for w in query.split() if len(w) > 2]
        skip_words = {"give", "generate", "recipe", "suggest", "for", "that", "with", "without", "make", "want", "need", "some", "this", "like", "please", "can", "you", "not", "have", "don't", "dont", "avoid"}
        new_words = [w for w in words if w not in skip_words and w not in clean_avoid]
        retrieval_parts.extend(new_words)

    # Clean duplicates
    clean_parts = []
    for p in retrieval_parts:
        if p not in clean_parts:
            clean_parts.append(p)

    final_query_str = " ".join(clean_parts).strip()

    # Append avoidance string cleanly if present
    if clean_avoid:
        final_query_str += " without " + ", ".join(clean_avoid)

    if not final_query_str.strip():
        final_query_str = query

    return final_query_str.strip()
