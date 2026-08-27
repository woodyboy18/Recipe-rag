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

    # 2. Extract Avoided Ingredients (Conjunction splitting enabled)
    ingredients_to_avoid = []
    avoid_patterns = [
        r"\b(?:without|no|don't have|do not have|dont have|have no|has no|avoid|exclude|skip|remove|dont want|don't want|allergic to)\s+([a-zA-Z0-9 ,'\-]+)",
        r"\b([a-zA-Z]+)\s+free\b"
    ]

    for pattern in avoid_patterns:
        for match in re.finditer(pattern, query_lower):
            raw_avoid_clause = match.group(1).strip()
            # Clean filler trailing words
            raw_avoid_clause = re.sub(r"\b(please|thanks|in it|for that|recipes?|substitutes?|anything|add)\b", "", raw_avoid_clause).strip()
            # Split conjunctions like "eggs and milk", "peanuts, almonds or cashew"
            items = re.split(r"\s*(?:,|and|or|&|\+)\s*", raw_avoid_clause)
            for item in items:
                norm = normalize_ingredient(item)
                if norm and norm not in STOP_WORDS and norm not in ingredients_to_avoid:
                    ingredients_to_avoid.append(norm)

    # 3. Extract Positive / Required / Available Ingredients
    ingredients_to_include = []
    available_ingredients = []

    include_patterns = [
        r"\b(?:with|using|containing|from|made of|features?)\s+([a-zA-Z0-9 ,'\-]+)",
        r"\b(?:i have|got|only have)\s+([a-zA-Z0-9 ,'\-]+)"
    ]

    for pattern in include_patterns:
        for match in re.finditer(pattern, query_lower):
            raw_clause = match.group(1).strip()
            # Stop clause if an avoidance word begins
            raw_clause = re.split(r"\b(?:but|without|no|except|avoiding)\b", raw_clause)[0].strip()
            items = re.split(r"\s*(?:,|and|or|&|\+)\s*", raw_clause)
            for item in items:
                norm = normalize_ingredient(item)
                if norm and norm not in STOP_WORDS and norm not in ingredients_to_avoid:
                    if norm not in ingredients_to_include:
                        ingredients_to_include.append(norm)
                    if "have" in pattern or "got" in pattern:
                        if norm not in available_ingredients:
                            available_ingredients.append(norm)

    # Deduplicate while preserving order
    ingredients_to_avoid = list(dict.fromkeys(ingredients_to_avoid))
    ingredients_to_include = list(dict.fromkeys(ingredients_to_include))
    available_ingredients = list(dict.fromkeys(available_ingredients))

    # 4. Meal Type
    meal = None
    meals = ["breakfast", "lunch", "dinner", "snack", "dessert", "appetizer", "soup", "salad"]
    for m in meals:
        if m in query_lower:
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
