import re
from typing import List, Union

# Words that should NEVER have trailing 's' or 'es' removed
NON_SINGULARIZABLE = {
    "glass", "rice", "molasses", "grass", "couscous", "hummus", "citrus",
    "watercress", "asparagus", "lemongrass", "oats", "swiss", "creme",
    "sea bass", "bass", "anise", "star anise", "horseradish", "dill weed"
}

# Known explicit alias transformations
ALIAS_MAP = {
    "strawberries": "strawberry",
    "blueberries": "blueberry",
    "raspberries": "raspberry",
    "blackberries": "blackberry",
    "cherries": "cherry",
    "tomatoes": "tomato",
    "potatoes": "potato",
    "eggs": "egg",
    "fresh strawberry": "strawberry",
    "frozen strawberry": "strawberry",
    "frozen strawberries": "strawberry",
    "whole milk": "milk",
    "skimmed milk": "milk",
    "skim milk": "milk",
    "unsalted butter": "butter",
    "salted butter": "butter",
    "extra virgin olive oil": "olive oil",
}

# Measurement units to strip out
UNITS = {
    "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon", "teaspoons",
    "g", "gram", "grams", "kg", "kilogram", "kilograms", "oz", "ounce", "ounces",
    "lb", "lbs", "pound", "pounds", "ml", "milliliter", "milliliters", "l", "liter", "liters",
    "pinch", "pinches", "clove", "cloves", "slice", "slices", "piece", "pieces",
    "handful", "handfuls", "can", "cans", "bottle", "bottles", "dash", "dashes",
    "head", "heads", "bunch", "bunches", "container", "package", "pkt", "drop", "drops"
}

# Preparation & descriptor words to strip out
DESCRIPTORS = {
    "fresh", "frozen", "raw", "cooked", "dried", "dry", "ground", "grated", "shredded",
    "whole", "unsalted", "salted", "extra", "virgin", "organic", "skimmed", "skim",
    "chopped", "diced", "minced", "sliced", "peeled", "crushed", "melted", "warm",
    "cold", "hot", "small", "medium", "large", "finely", "coarsely", "pureed",
    "canned", "packed", "toasted", "roasted", "boiled", "fried", "baked", "softened"
}


def normalize_ingredient(raw: str) -> str:
    """
    Normalizes an ingredient string into its canonical representation.
    - Strips amounts, units, prep terms, adjectives, punctuation, brackets.
    - Converts plurals to singular conservatively without breaking words like 'glass', 'rice', 'molasses'.
    """
    if not raw or not isinstance(raw, str):
        return ""

    text = raw.lower().strip()

    # Remove text in parentheses or brackets
    text = re.sub(r"[\(\[\{].*?[\)\]\}]", "", text)

    # Check explicit alias map first
    if text in ALIAS_MAP:
        return ALIAS_MAP[text]

    # Remove quantities (e.g. 1/2, 1.5, 2, 1-2)
    text = re.sub(r"\b\d+[\/\.]?\d*\b", "", text)
    text = re.sub(r"[\d\+\-\*\/]", "", text)

    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    # Split into tokens
    tokens = text.split()
    cleaned_tokens = []

    for token in tokens:
        if token in UNITS or token in DESCRIPTORS:
            continue
        cleaned_tokens.append(token)

    if not cleaned_tokens:
        # Fallback if all tokens were units/descriptors
        cleaned_tokens = [t for t in tokens if not re.match(r"^\d+$", t)]

    phrase = " ".join(cleaned_tokens).strip()

    if phrase in ALIAS_MAP:
        return ALIAS_MAP[phrase]

    # Apply singularization to individual words in the phrase
    words = phrase.split()
    singular_words = []
    for word in words:
        singular_words.append(_singularize_word(word))

    final_result = " ".join(singular_words).strip()
    return final_result


def _singularize_word(word: str) -> str:
    if len(word) <= 3 or word in NON_SINGULARIZABLE:
        return word

    if word in ALIAS_MAP:
        return ALIAS_MAP[word]

    # Rule: -ies -> -y (e.g., strawberries -> strawberry, berries -> berry)
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"

    # Rule: -es for words ending in -es (e.g., tomatoes -> tomato, potatoes -> potato)
    if word.endswith("es") and len(word) > 4:
        if word.endswith("tomatoes"):
            return word[:-2]
        if word.endswith("potatoes"):
            return word[:-2]
        if word.endswith("ches") or word.endswith("shes") or word.endswith("oxes") or word.endswith("axes"):
            return word[:-2]

    # Rule: -s -> remove 's' (e.g., eggs -> egg, carrots -> carrot)
    if word.endswith("s") and not word.endswith("ss") and not word.endswith("is") and not word.endswith("us"):
        return word[:-1]

    return word


def normalize_ingredient_list(ingredients: List[Union[str, dict]]) -> List[str]:
    """
    Normalizes a list of ingredients, deduplicating non-empty canonical strings.
    """
    normalized = []
    for item in ingredients:
        if isinstance(item, dict):
            raw_str = item.get("name", "")
        else:
            raw_str = str(item)
        
        norm = normalize_ingredient(raw_str)
        if norm and norm not in normalized:
            normalized.append(norm)

    return normalized
