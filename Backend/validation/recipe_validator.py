import re
from typing import Dict, Any, List, Set, Optional
from core.schemas import QuerySpec
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list

class ValidationResult:
    def __init__(
        self,
        is_valid: bool = True,
        errors: List[str] = None,
        warnings: List[str] = None,
        constraint_score: float = 1.0,
        grounding_score: float = 1.0,
        ingredient_step_consistency: float = 1.0,
        compatibility_score: float = 1.0
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.constraint_score = round(constraint_score, 3)
        self.grounding_score = round(grounding_score, 3)
        self.ingredient_step_consistency = round(ingredient_step_consistency, 3)
        self.compatibility_score = round(compatibility_score, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "constraint_score": self.constraint_score,
            "grounding_score": self.grounding_score,
            "ingredient_step_consistency": self.ingredient_step_consistency,
            "compatibility_score": self.compatibility_score
        }


def validate_synthesized_recipe(
    recipe_dict: Dict[str, Any],
    query_spec: QuerySpec,
    parent_recipes: List[Dict[str, Any]] = None,
    compatibility_graph = None
) -> ValidationResult:
    """
    Performs hard constraint checks and calculates grounding, consistency, and compatibility scores.
    Hard failures reject candidate recipe outright.
    """
    errors = []
    warnings = []
    is_valid = True

    if not recipe_dict or not isinstance(recipe_dict, dict):
        return ValidationResult(is_valid=False, errors=["Empty recipe structure"])

    title = recipe_dict.get("title", "")
    raw_ings = recipe_dict.get("ingredients", [])
    raw_insts = recipe_dict.get("instructions", [])

    # 1. Structural Checks
    if not title or len(str(title).strip()) < 2:
        errors.append("Recipe title is missing or too short")
        is_valid = False

    if not raw_ings or len(raw_ings) == 0:
        errors.append("Recipe ingredient list is empty")
        is_valid = False

    if not raw_insts or len(raw_insts) == 0:
        errors.append("Recipe instruction list is empty")
        is_valid = False

    if not is_valid:
        return ValidationResult(is_valid=False, errors=errors, constraint_score=0.0)

    # Normalize recipe ingredients
    recipe_norm_ings = normalize_ingredient_list(raw_ings)
    recipe_ing_set = set(recipe_norm_ings)

    # 2. Hard Constraint Checks: Required Ingredients
    req_ings = set(normalize_ingredient_list(query_spec.ingredients_to_include))
    missing_req = req_ings - recipe_ing_set

    # Also check if any required ingredient is present via substring match
    final_missing_req = []
    for r in missing_req:
        matched = any(r in ing or ing in r for ing in recipe_norm_ings)
        if not matched:
            final_missing_req.append(r)

    if final_missing_req:
        errors.append(f"Missing mandatory required ingredients: {', '.join(final_missing_req)}")
        is_valid = False

    # 3. Hard Constraint Checks: Avoided Ingredients
    avoid_ings = set(normalize_ingredient_list(query_spec.ingredients_to_avoid))
    violated_avoid = []
    for a in avoid_ings:
        for ing in recipe_norm_ings:
            pattern = r"\b" + re.escape(a) + r"(?:s|es)?\b"
            if re.search(pattern, ing):
                violated_avoid.append(a)

    if violated_avoid:
        errors.append(f"Contains forbidden ingredients: {', '.join(set(violated_avoid))}")
        is_valid = False

    constraint_score = 1.0 if (not final_missing_req and not violated_avoid) else 0.0

    # 4. Ingredient-Instruction Consistency Check
    # Check that required ingredients appear in instructions text
    combined_inst_text = " ".join([str(step).lower() for step in raw_insts])
    unused_req_in_instructions = []
    for req in req_ings:
        if req not in combined_inst_text and not any(req in w for w in combined_inst_text.split()):
            unused_req_in_instructions.append(req)

    if unused_req_in_instructions:
        errors.append(f"Required ingredient(s) never used in instructions: {', '.join(unused_req_in_instructions)}")
        is_valid = False

    # Check how many listed ingredients appear in instructions
    used_count = 0
    for ing in recipe_norm_ings:
        if ing in combined_inst_text or any(w in combined_inst_text for w in ing.split()):
            used_count += 1
        elif len(ing) > 3 and ing[:-1] in combined_inst_text:
            used_count += 1

    consistency_score = (used_count / len(recipe_norm_ings)) if recipe_norm_ings else 1.0

    # 5. Grounding Score against Parent Evidence & Compatibility Graph
    parent_ings_set = set()
    if parent_recipes:
        for p in parent_recipes:
            p_ings = p.get("normalized_ingredients", [])
            if not p_ings and "ingredients" in p:
                raw_p = p["ingredients"]
                p_ings = normalize_ingredient_list([i.strip() for i in raw_p.split(",")] if isinstance(raw_p, str) else raw_p)
            parent_ings_set.update(p_ings)

    grounded_count = 0
    for ing in recipe_norm_ings:
        if ing in parent_ings_set or ing in req_ings:
            grounded_count += 1
        elif compatibility_graph and any(compatibility_graph.compatibility_score(ing, p_ing) > 0.1 for p_ing in parent_ings_set):
            grounded_count += 1

    grounding_score = (grounded_count / len(recipe_norm_ings)) if recipe_norm_ings else 1.0

    # 6. Compatibility Score
    comp_score = 1.0
    if compatibility_graph:
        comp_score = compatibility_graph.recipe_compatibility_score(recipe_norm_ings)
        if comp_score < 0.15:
            warnings.append("Low compatibility score between ingredients")

    # Soft Warnings
    if len(raw_insts) < 2:
        warnings.append("Recipe contains very few instruction steps")

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        constraint_score=constraint_score,
        grounding_score=grounding_score,
        ingredient_step_consistency=consistency_score,
        compatibility_score=comp_score
    )
