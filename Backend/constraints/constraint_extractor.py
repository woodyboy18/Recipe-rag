import re
from typing import Dict, Any, List, Optional
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list
from core.schemas import QuerySpec

MEAT_INGREDIENTS = [
    "chicken", "beef", "pork", "mutton", "lamb", "fish", "prawn", "seafood",
    "bacon", "turkey", "ham", "sausage", "meat"
]

STOP_WORDS = {
    "give", "recipe", "recipes", "for", "me", "suggest", "that", "make", "want", "need",
    "some", "this", "like", "please", "can", "you", "a", "an", "the", "in", "it", "to",
    "something", "anything", "dish", "food", "create", "show", "find", "search"
}

def parse_query_to_spec(query: str, requested_mode: str = "auto", novelty_level: str = "balanced") -> QuerySpec:
    """
    Parses a user query string into a structured QuerySpec dataclass.
    Handles mode detection, positive/required ingredient extraction, avoidance phrase extraction with conjunction splitting,
    dietary preferences, meal type, cuisine, time, and calories.
    """
    query_lower = query.lower().strip()

    # 1. Mode / Intent Detection
    detected_intent = "auto"
    if any(k in query_lower for k in ["create a new", "invent", "unique", "creative", "new recipe", "new dessert", "new dish", "synthesize"]):
        detected_intent = "novel"
    elif any(k in query_lower for k in ["show me", "find me", "recommend", "search for", "look for", "show", "find"]):
        detected_intent = "find"

    # Caller requested_mode overrides auto-detected intent if requested_mode != "auto"
    effective_mode = requested_mode if requested_mode in ["find", "novel"] else detected_intent

    # 2. Extract Substitution Constraints (e.g. substitute butter with olive oil, replace milk with almond milk)
    ingredients_to_avoid = []
    ingredients_to_include = []
    available_ingredients = []

    sub_patterns = [
        r"\b(?:substitute|replace|swap)\s+([a-zA-Z0-9 ,'\-]+?)\s+(?:with|for|by)\s+([a-zA-Z0-9 ,'\-]+)",
        r"\b(?:use|put)\s+([a-zA-Z0-9 ,'\-]+?)\s+instead of\s+([a-zA-Z0-9 ,'\-]+)"
    ]

    for pattern in sub_patterns:
        for match in re.finditer(pattern, query_lower):
            if "instead of" in pattern:
                inc_clause, avoid_clause = match.group(1), match.group(2)
            else:
                avoid_clause, inc_clause = match.group(1), match.group(2)

            # Clean clauses up to first stop word / punctuation
            clean_avoid = re.split(r"\b(?:but|and|with|substitute|replace|using|no|without|avoid)\b", avoid_clause)[0].strip()
            clean_inc = re.split(r"\b(?:but|and|substitute|replace|using|no|without|avoid)\b", inc_clause)[0].strip()

            norm_avoid = normalize_ingredient(clean_avoid)
            norm_inc = normalize_ingredient(clean_inc)

            if norm_avoid and norm_avoid not in ingredients_to_avoid:
                ingredients_to_avoid.append(norm_avoid)
            if norm_inc and norm_inc not in ingredients_to_include:
                ingredients_to_include.append(norm_inc)

    # 3. Extract Avoided Ingredients
    avoid_patterns = [
        r"\b(?:without|no|don't have|do not have|dont have|have no|has no|avoid|exclude|skip|remove|dont want|don't want|allergic to)\s+([a-zA-Z0-9 ,'\-]+)",
        r"\b([a-zA-Z]+)\s+free\b"
    ]

    for pattern in avoid_patterns:
        for match in re.finditer(pattern, query_lower):
            raw_avoid_clause = match.group(1).strip()
            # Truncate at clause breaks
            raw_avoid_clause = re.split(r"\b(?:but|and|with|substitute|replace|using)\b", raw_avoid_clause)[0].strip()
            raw_avoid_clause = re.sub(r"\b(please|thanks|in it|for that|recipes?|substitutes?|anything|add)\b", "", raw_avoid_clause).strip()
            items = re.split(r"\s*(?:,|and|or|&|\+)\s*", raw_avoid_clause)
            for item in items:
                norm = normalize_ingredient(item)
                if norm and norm not in STOP_WORDS and norm not in ingredients_to_avoid and len(norm) <= 25:
                    ingredients_to_avoid.append(norm)

    # 4. Extract Positive / Required / Available Ingredients
    include_patterns = [
        r"\b(?:with|using|containing|from|made of|features?|combining|combines?|including|includes?|of|for)\s+([a-zA-Z0-9 ,'\-]+)",
        r"\b(?:i have|got|only have)\s+([a-zA-Z0-9 ,'\-]+)"
    ]

    for pattern in include_patterns:
        for match in re.finditer(pattern, query_lower):
            raw_clause = match.group(1).strip()
            # Stop clause if an avoidance or substitution word begins
            raw_clause = re.split(r"\b(?:but|without|no|except|avoiding|avoid|substitute|replace|swap|instead)\b", raw_clause)[0].strip()
            items = re.split(r"\s*(?:,|and|or|&|\+)\s*", raw_clause)
            for item in items:
                norm = normalize_ingredient(item)
                if norm and norm not in STOP_WORDS and norm not in ingredients_to_avoid and len(norm) <= 25:
                    if norm not in ingredients_to_include:
                        ingredients_to_include.append(norm)
                    if "have" in pattern or "got" in pattern:
                        if norm not in available_ingredients:
                            available_ingredients.append(norm)

    # Fallback for direct ingredient queries (e.g. "asafoetida", "hing", "paneer and chicken")
    if not ingredients_to_include:
        clean_q = re.sub(r"\b(?:give|me|recipe|recipes|show|find|search|suggest|make|create|new|dish|food|item|items|please|can|you)\b", "", query_lower).strip()
        if clean_q and not any(av in query_lower for av in ["without", "no ", "avoid", "don't", "dont"]):
            items = re.split(r"\s*(?:,|and|or|&|\+)\s*", clean_q)
            for item in items:
                norm = normalize_ingredient(item)
                if norm and norm not in STOP_WORDS and norm not in ingredients_to_avoid and len(norm) <= 25:
                    if norm not in ingredients_to_include:
                        ingredients_to_include.append(norm)

    # Deduplicate while preserving order
    ingredients_to_avoid = list(dict.fromkeys(ingredients_to_avoid))
    ingredients_to_include = list(dict.fromkeys(ingredients_to_include))
    available_ingredients = list(dict.fromkeys(available_ingredients))

    # 4. Meal Type
    meal = None
    meals = ["breakfast", "lunch", "dinner", "snack", "dessert", "appetizer", "soup", "salad", "smoothie", "beverage", "drink"]
    for m in meals:
        if m in query_lower or (m == "smoothie" and "smotthie" in query_lower):
            meal = m
            break

    # 5. Diet
    diet = None
    is_veg = False
    if re.search(r"\b(?:veg|vegetarian|pure veg|veg\.|vegan)\b", query_lower):
        is_veg = True
        diet = "vegetarian" if "vegan" not in query_lower else "vegan"

    diets = ["keto", "low carb", "gluten free"]
    for d in diets:
        if d in query_lower:
            diet = d
            break

    # Automatic Meat Avoidance for Veg queries
    if is_veg:
        for m in MEAT_INGREDIENTS:
            norm_m = normalize_ingredient(m)
            if norm_m not in ingredients_to_avoid:
                ingredients_to_avoid.append(norm_m)

    # 6. Cuisine
    cuisine = None
    cuisines = ["indian", "italian", "chinese", "mexican", "thai", "american", "japanese", "french", "mediterranean"]
    for c in cuisines:
        if c in query_lower:
            cuisine = c
            break

    # 7. Time & Calories
    max_time = None
    time_match = re.search(r'(\d+)\s*(min|mins|minute|minutes)', query_lower)
    if time_match:
        max_time = int(time_match.group(1))

    max_calories = None
    cal_match = re.search(r'(\d+)\s*(cal|kcal|calories)', query_lower)
    if cal_match:
        max_calories = int(cal_match.group(1))

    return QuerySpec(
        original_query=query,
        intent=detected_intent,
        mode=effective_mode,
        ingredients_to_include=ingredients_to_include,
        available_ingredients=available_ingredients,
        ingredients_to_avoid=ingredients_to_avoid,
        meal=meal,
        diet=diet,
        cuisine=cuisine,
        max_time=max_time,
        max_calories=max_calories,
        novelty_level=novelty_level
    )


def extract_constraints(query: str) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper returning a dictionary format.
    """
    spec = parse_query_to_spec(query)
    return {
        "meal": spec.meal,
        "diet": spec.diet,
        "protein": None,
        "time": spec.max_time,
        "calories": spec.max_calories,
        "ingredients_to_avoid": spec.ingredients_to_avoid,
        "ingredients_to_include": spec.ingredients_to_include,
        "user_available_ingredients": spec.available_ingredients,
        "cuisine": spec.cuisine,
        "allow_substitutions": True,
        "mode": spec.mode,
        "intent": spec.intent
    }


def merge_constraints(previous_constraints: dict, current_constraints: dict) -> dict:
    if not previous_constraints:
        return current_constraints

    merged = previous_constraints.copy()
    for key, value in current_constraints.items():
        if value is None:
            continue
        if isinstance(value, list):
            merged.setdefault(key, [])
            for item in value:
                if item not in merged[key]:
                    merged[key].append(item)
        else:
            merged[key] = value

    return merged
