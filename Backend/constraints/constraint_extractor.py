import re

MEAT_INGREDIENTS = [
    "chicken", "beef", "pork", "mutton", "lamb", "fish", "prawn", "seafood",
    "bacon", "turkey", "ham", "sausage", "meat"
]

def extract_constraints(query: str):
    query_lower = query.lower()

    constraints = {
        "meal": None,
        "diet": None,
        "protein": None,
        "time": None,
        "calories": None,
        "ingredients_to_avoid": [],
        "user_available_ingredients": [],
        "cuisine": None,
        "allow_substitutions": True
    }

    # ---------------- Check Available Ingredients ----------------
    avail_match = re.search(r"\b(?:i have|with|using|got|only have)\s+([a-zA-Z ,]+)", query_lower)
    if avail_match:
        raw_avail = avail_match.group(1).strip()
        stop_words = {"give", "recipe", "for", "me", "suggest", "that", "make", "want", "need", "some", "this", "like", "please"}
        tokens = [t.strip() for t in re.split(r"[,\s\+]+", raw_avail) if t.strip()]
        avail_list = [t for t in tokens if len(t) > 2 and t not in stop_words and t not in MEAT_INGREDIENTS]
        constraints["user_available_ingredients"] = avail_list

    # ---------------- Check Substitution Opt-Out ----------------
    no_sub_patterns = [
        r"\bno\s+substitut", r"\bdon'?t\s+substitut", r"\bdo\s+not\s+add", r"\bdon'?t\s+add",
        r"\bwithout\s+substitut", r"\bresist", r"\bno\s+replacement", r"\bdon'?t\s+replace"
    ]
    for p in no_sub_patterns:
        if re.search(p, query_lower):
            constraints["allow_substitutions"] = False
            break

    # ---------------- Meal Type ----------------
    meals = ["breakfast", "lunch", "dinner", "snack", "dessert"]
    for meal in meals:
        if meal in query_lower:
            constraints["meal"] = meal
            break

    # ---------------- Diet ----------------
    is_veg = False
    if re.search(r"\b(?:veg|vegetarian|pure veg|veg\.|vegan)\b", query_lower):
        is_veg = True
        constraints["diet"] = "vegetarian"
    elif "vegan" in query_lower:
        is_veg = True
        constraints["diet"] = "vegan"

    diets = ["keto", "low carb", "gluten free"]
    for diet in diets:
        if diet in query_lower:
            constraints["diet"] = diet
            break

    # ---------------- Protein ----------------
    if "high protein" in query_lower:
        constraints["protein"] = "high"
    elif "low protein" in query_lower:
        constraints["protein"] = "low"

    # ---------------- Cooking Time ----------------
    match = re.search(r'(\d+)\s*(min|mins|minute|minutes)', query_lower)
    if match:
        constraints["time"] = int(match.group(1))

    # ---------------- Calories ----------------
    match = re.search(r'(\d+)\s*(cal|kcal|calories)', query_lower)
    if match:
        constraints["calories"] = int(match.group(1))

    # ---------------- Ingredient Avoidance ----------------
    avoid_patterns = [
        r"\b(?:without|no|don't have|do not have|dont have|have no|has no|avoid|exclude|skip|remove|dont want|don't want)\s+([a-zA-Z ]+)",
        r"\b([a-zA-Z]+)\s+free\b"
    ]

    for pattern in avoid_patterns:
        matches = re.finditer(pattern, query_lower)
        for match in matches:
            raw_ing = match.group(1).strip()
            cleaned_ing = re.sub(r"\b(please|thanks|in it|for that|recipes?|substitutes?|anything|add)\b", "", raw_ing).strip()
            if cleaned_ing and len(cleaned_ing) > 1:
                constraints["ingredients_to_avoid"].append(cleaned_ing)
                if cleaned_ing.endswith("s") and len(cleaned_ing) > 3:
                    constraints["ingredients_to_avoid"].append(cleaned_ing[:-1])
                elif not cleaned_ing.endswith("s"):
                    constraints["ingredients_to_avoid"].append(cleaned_ing + "s")

    # ---------------- Automatic Meat Avoidance for Veg / Plant Queries ----------------
    has_meat_mention = any(m in query_lower for m in MEAT_INGREDIENTS)
    has_plant_mention = any(p in query_lower for p in ["soyabean", "soybean", "tofu", "paneer", "dal", "lentil", "veggie", "vegetable", "oats"])
    is_addition_query = any(k in query_lower for k in ["add ", "with ", "plus ", "include "])

    # ONLY apply automatic meat avoidance for explicit veg requests or standalone plant queries
    if is_veg or (has_plant_mention and not has_meat_mention and not is_addition_query):
        for m in MEAT_INGREDIENTS:
            if m not in constraints["ingredients_to_avoid"]:
                constraints["ingredients_to_avoid"].append(m)

    # ---------------- Cuisine ----------------
    cuisines = ["indian", "italian", "chinese", "mexican", "thai", "american"]
    for cuisine in cuisines:
        if cuisine in query_lower:
            constraints["cuisine"] = cuisine
            break

    # Deduplicate
    constraints["ingredients_to_avoid"] = list(dict.fromkeys(constraints["ingredients_to_avoid"]))

    return constraints


def merge_constraints(previous_constraints, current_constraints):
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
