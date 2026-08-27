"""
USDA FoodData Central Nutritional & Flavour Substitution Engine

Provides standard USDA FoodData Central protein, calorie, and macro-equivalent 
substitutions for recipe adaptation when ingredients are unavailable or avoided.
"""

# USDA FoodData Central Nutritional Profiles (per 100g standard measure)
USDA_NUTRITION_DATABASE = {
    "egg": {
        "name": "Egg (whole, raw)",
        "protein_per_100g": 12.6,
        "calories_per_100g": 143,
        "category": "poultry/dairy",
        "flavor_profile": "savory / binding",
        "substitutes": [
            {"name": "Tofu (Firm)", "protein_per_100g": 14.0, "ratio": 1.0, "note": "USDA Standard Tofu (Soybean Curd)"},
            {"name": "Paneer (Cottage Cheese)", "protein_per_100g": 18.3, "ratio": 0.8, "note": "USDA Cottage Cheese / Paneer"},
            {"name": "Soya Chunks", "protein_per_100g": 52.0, "ratio": 0.3, "note": "USDA Defatted Soy Flour / Chunks"},
            {"name": "Chickpeas (Boiled)", "protein_per_100g": 8.9, "ratio": 1.4, "note": "USDA Chickpea / Garbanzo"}
        ]
    },
    "eggs": {
        "name": "Eggs (whole, raw)",
        "protein_per_100g": 12.6,
        "calories_per_100g": 143,
        "category": "poultry/dairy",
        "flavor_profile": "savory / binding",
        "substitutes": [
            {"name": "Tofu (Firm)", "protein_per_100g": 14.0, "ratio": 1.0, "note": "USDA Standard Tofu"},
            {"name": "Paneer", "protein_per_100g": 18.3, "ratio": 0.8, "note": "USDA Cottage Cheese / Paneer"},
            {"name": "Soya Chunks", "protein_per_100g": 52.0, "ratio": 0.3, "note": "USDA High-Protein Soy Chunks"}
        ]
    },
    "chicken": {
        "name": "Chicken Breast (boneless, raw)",
        "protein_per_100g": 23.1,
        "calories_per_100g": 110,
        "category": "meat",
        "flavor_profile": "savory / umami / meaty",
        "substitutes": [
            {"name": "Soya Chunks (Soya Nuggets)", "protein_per_100g": 52.0, "ratio": 0.45, "note": "USDA Soya Protein Concentrate (High protein match)"},
            {"name": "Paneer", "protein_per_100g": 18.3, "ratio": 1.25, "note": "USDA Cottage Cheese / Paneer"},
            {"name": "Tofu (Extra Firm)", "protein_per_100g": 14.0, "ratio": 1.65, "note": "USDA Firm Tofu"},
            {"name": "Button Mushrooms", "protein_per_100g": 3.1, "ratio": 1.0, "note": "USDA Mushroom (Texture & Umami Match)"}
        ]
    },
    "mutton": {
        "name": "Lamb / Mutton",
        "protein_per_100g": 25.0,
        "calories_per_100g": 294,
        "category": "meat",
        "flavor_profile": "rich savory / umami",
        "substitutes": [
            {"name": "Soya Chunks", "protein_per_100g": 52.0, "ratio": 0.48, "note": "USDA High-Protein Soya Match"},
            {"name": "Paneer Cubes", "protein_per_100g": 18.3, "ratio": 1.35, "note": "USDA Paneer / Indian Cottage Cheese"}
        ]
    },
    "milk": {
        "name": "Whole Milk",
        "protein_per_100g": 3.4,
        "calories_per_100g": 61,
        "category": "dairy",
        "flavor_profile": "creamy / neutral",
        "substitutes": [
            {"name": "Soy Milk", "protein_per_100g": 3.3, "ratio": 1.0, "note": "USDA Fortified Soy Milk (Closest protein match)"},
            {"name": "Almond Milk", "protein_per_100g": 1.0, "ratio": 1.0, "note": "USDA Almond Milk"},
            {"name": "Coconut Milk", "protein_per_100g": 2.3, "ratio": 1.0, "note": "USDA Coconut Milk"}
        ]
    },
    "yogurt": {
        "name": "Plain Yogurt",
        "protein_per_100g": 3.5,
        "calories_per_100g": 61,
        "category": "dairy",
        "flavor_profile": "tangy / creamy",
        "substitutes": [
            {"name": "Soy Yogurt", "protein_per_100g": 3.5, "ratio": 1.0, "note": "USDA Soy Yogurt"},
            {"name": "Cashew Yogurt", "protein_per_100g": 3.0, "ratio": 1.0, "note": "USDA Nut-based Yogurt"}
        ]
    },
    "butter": {
        "name": "Butter",
        "protein_per_100g": 0.9,
        "calories_per_100g": 717,
        "category": "fat",
        "flavor_profile": "rich / fatty",
        "substitutes": [
            {"name": "Olive Oil", "protein_per_100g": 0.0, "ratio": 0.8, "note": "USDA Extra Virgin Olive Oil"},
            {"name": "Avocado Oil", "protein_per_100g": 0.0, "ratio": 0.8, "note": "USDA Avocado Oil"}
        ]
    }
}


def get_usda_substitution_advice(avoided_ingredients, allow_substitutions=True):
    """
    Generate USDA-aligned protein and flavour substitution advice for avoided ingredients.
    Returns a dict with structured substitution details or empty list if user resisted substitutions.
    """
    if not allow_substitutions or not avoided_ingredients:
        return {
            "allow_substitutions": False,
            "substitutions": [],
            "message": "Strict filtering applied: No ingredient substitutions added as per your request."
        }

    substitutions_found = []

    for ing in avoided_ingredients:
        key = ing.lower().strip()
        # Find matching key in USDA database
        matched_key = None
        for db_key in USDA_NUTRITION_DATABASE:
            if db_key in key or key in db_key:
                matched_key = db_key
                break

        if matched_key:
            data = USDA_NUTRITION_DATABASE[matched_key]
            best_sub = data["substitutes"][0]
            
            substitutions_found.append({
                "original_ingredient": data["name"],
                "original_protein": f"{data['protein_per_100g']}g / 100g (USDA)",
                "substitute_name": best_sub["name"],
                "substitute_protein": f"{best_sub['protein_per_100g']}g / 100g (USDA)",
                "flavor_match": data["flavor_profile"],
                "note": best_sub["note"]
            })

    return {
        "allow_substitutions": True,
        "substitutions": substitutions_found,
        "message": f"Applied USDA FoodData Central protein-equivalent substitutions." if substitutions_found else ""
    }
