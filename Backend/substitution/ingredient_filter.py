import re

def filter_recipes(docs, avoid_ingredients):
    """
    Remove recipes containing ingredients the user wants to avoid.
    Matches word boundaries and singular/plural variations.
    """
    if not avoid_ingredients:
        return docs

    filtered_docs = []

    for doc in docs:
        recipe = doc.lower()
        remove = False

        for ingredient in avoid_ingredients:
            ing = ingredient.lower().strip()
            if not ing:
                continue

            # Use word boundary matching for precise ingredient filtering
            pattern = r"\b" + re.escape(ing) + r"(?:s|es)?\b"
            if re.search(pattern, recipe):
                remove = True
                break

        if not remove:
            filtered_docs.append(doc)

    # If every recipe was filtered out, return docs that have the MINIMUM matches of avoided ingredients
    if not filtered_docs and docs:
        doc_scores = []
        for doc in docs:
            recipe = doc.lower()
            match_count = 0
            for ingredient in avoid_ingredients:
                ing = ingredient.lower().strip()
                if ing and re.search(r"\b" + re.escape(ing) + r"(?:s|es)?\b", recipe):
                    match_count += 1
            doc_scores.append((match_count, doc))

        doc_scores.sort(key=lambda x: x[0])
        filtered_docs = [d for count, d in doc_scores if count == doc_scores[0][0]]

    return filtered_docs
