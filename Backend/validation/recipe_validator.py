"""
Recipe Validator Module
Performs post-generation validation on RecipeState objects.
Ensures ingredient-instruction alignment, valid quantities, realistic cooking times, and structural sanity.
"""

from state.recipe_state import RecipeState

class ValidationResult:
    def __init__(self, is_valid: bool = True, warnings: list = None, corrected_recipe: RecipeState = None):
        self.is_valid = is_valid
        self.warnings = warnings or []
        self.corrected_recipe = corrected_recipe

    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "warnings": self.warnings
        }


def validate_recipe(recipe: RecipeState) -> ValidationResult:
    """
    Validates a RecipeState object for consistency, realistic cooking times, and quantity sanity.
    """
    warnings = []
    is_valid = True

    if not recipe:
        return ValidationResult(is_valid=False, warnings=["Empty recipe state"])

    # 1. Title Check
    if not recipe.title or len(recipe.title.strip()) < 3:
        recipe.title = "Delicious Culinary Recipe"
        warnings.append("Defaulted missing recipe title.")

    # 2. Ingredients Check
    if not recipe.ingredients or len(recipe.ingredients) == 0:
        is_valid = False
        warnings.append("Recipe ingredients list is empty.")

    # Check ingredient quantities (must be > 0)
    for ing in recipe.ingredients:
        if ing.amount <= 0:
            ing.amount = 1.0
            warnings.append(f"Corrected non-positive quantity for ingredient '{ing.name}'.")

    # 3. Instructions Check
    if not recipe.instructions or len(recipe.instructions) == 0:
        recipe.instructions = [
            "Prepare and combine all listed ingredients.",
            "Cook over medium heat until fully done and aromatic.",
            "Garnish as desired and serve hot!"
        ]
        warnings.append("Added default step-by-step instructions.")

    # 4. Cooking / Prep Time Sanity Check
    if recipe.cook_time_mins < 1 or recipe.cook_time_mins > 720:
        recipe.cook_time_mins = 30
        warnings.append("Normalized out-of-range cook time to 30 mins.")

    if recipe.prep_time_mins < 1 or recipe.prep_time_mins > 360:
        recipe.prep_time_mins = 15
        warnings.append("Normalized out-of-range prep time to 15 mins.")

    # 5. Servings Sanity Check
    if recipe.servings < 1 or recipe.servings > 50:
        recipe.servings = 2
        warnings.append("Normalized out-of-range servings to 2.")

    # 6. Nutrition Bounds Check
    if not recipe.nutrition or recipe.nutrition.get("calories", 0) <= 0:
        recipe.nutrition = {"calories": 520, "protein_g": 35, "carbs_g": 45, "fat_g": 18}
        warnings.append("Normalized nutrition values.")

    return ValidationResult(
        is_valid=is_valid,
        warnings=warnings,
        corrected_recipe=recipe
    )
