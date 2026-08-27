def filter_recipes(docs, avoid_ingredients):
    """
    Remove recipes containing ingredients the user wants to avoid.
    """

    if not avoid_ingredients:
        return docs

    filtered_docs = []

    for doc in docs:

        recipe = doc.lower()

        remove = False

        for ingredient in avoid_ingredients:

            if ingredient.lower() in recipe:
                remove = True
                break

        if not remove:
            filtered_docs.append(doc)

    return filtered_docs
