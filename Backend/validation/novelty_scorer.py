import pandas as pd
from typing import Dict, Any, List, Set, Tuple
from ingredients.normalizer import normalize_ingredient_list
from ingredients.ingredient_index import IngredientIndex

def compute_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def compute_technique_similarity(actions_a: List[str], actions_b: List[str]) -> float:
    if not actions_a or not actions_b:
        return 0.0
    set_a = set(actions_a)
    set_b = set(actions_b)
    return compute_jaccard_similarity(set_a, set_b)

def compute_novelty_score(
    recipe_dict: Dict[str, Any],
    df: pd.DataFrame,
    ingredient_index: IngredientIndex = None
) -> Dict[str, float]:
    """
    Computes composite novelty score relative to dataset recipes.
    0.7 * ingredient_novelty + 0.3 * technique_novelty.
    """
    raw_ings = recipe_dict.get("ingredients", [])
    norm_ings = set(normalize_ingredient_list(raw_ings))

    if not norm_ings:
        return {"ingredient_novelty": 0.0, "technique_novelty": 0.0, "novelty_score": 0.0, "max_dataset_similarity": 1.0}

    # Find dataset recipes sharing at least one ingredient to limit comparison pool
    comparison_pos = []
    if ingredient_index:
        rec_ids = set()
        for ing in norm_ings:
            if ing in ingredient_index.index:
                rec_ids.update(ingredient_index.index[ing])
        if "recipe_id" in df.columns:
            comparison_pos = df.index[df["recipe_id"].isin(rec_ids)].tolist()[:300]
        else:
            comparison_pos = [pos for pos in rec_ids if pos < len(df)][:300]

    if not comparison_pos:
        comparison_pos = list(range(min(500, len(df))))

    max_ing_sim = 0.0
    nearest_pos = None

    for pos in comparison_pos:
        row = df.iloc[pos]
        df_ings = row.get("normalized_ingredients", [])
        if not df_ings and "ingredients" in row:
            df_ings = normalize_ingredient_list([i.strip() for i in str(row["ingredients"]).split(",") if i.strip()])
        
        sim = compute_jaccard_similarity(norm_ings, set(df_ings))
        if sim > max_ing_sim:
            max_ing_sim = sim
            nearest_pos = pos

    ingredient_novelty = round(1.0 - max_ing_sim, 3)

    # Technique novelty
    gen_insts = recipe_dict.get("instructions", [])
    combined_insts = " ".join([str(s).lower() for s in gen_insts])
    common_actions = ["blend", "bake", "boil", "fry", "saute", "simmer", "whisk", "roast", "stir", "grill", "chill", "chop", "mix", "pour", "beat"]
    gen_actions = [a for a in common_actions if a in combined_insts]

    tech_sim = 0.0
    if nearest_pos is not None:
        nearest_row = df.iloc[nearest_pos]
        nearest_insts = str(nearest_row.get("instructions", "")).lower()
        nearest_actions = [a for a in common_actions if a in nearest_insts]
        tech_sim = compute_technique_similarity(gen_actions, nearest_actions)

    technique_novelty = round(1.0 - tech_sim, 3)

    composite_score = round((0.7 * ingredient_novelty) + (0.3 * technique_novelty), 3)

    return {
        "ingredient_novelty": ingredient_novelty,
        "technique_novelty": technique_novelty,
        "novelty_score": composite_score,
        "max_dataset_similarity": round(max_ing_sim, 3)
    }
