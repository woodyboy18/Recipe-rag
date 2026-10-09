"""
Taste-Aware & Function-Aware Ingredient Substitution Engine
Finds dynamic ingredient substitutions based on:
1. Taxonomy Category Hierarchy (e.g. Plant Protein, Dairy, Fat/Oil)
2. Culinary Functional Role (e.g. Binder, Thickener, Fat Source, Protein Base)
3. Taste & Flavor Profile (e.g. Umami/Savory, Sweet/Creamy, Tangy/Acidic)
4. Dataset Co-occurrence PPMI Compatibility
"""

from typing import List, Dict, Any, Optional
from ingredients.ontology import IngredientOntology

_ontology_instance: Optional[IngredientOntology] = None

def get_ontology() -> IngredientOntology:
    global _ontology_instance
    if _ontology_instance is None:
        _ontology_instance = IngredientOntology()
    return _ontology_instance


def find_substitutes(
    ingredient_name: str,
    avoided_ingredients: List[str] = None,
    diet_preference: str = None,
    compatibility_graph = None
) -> List[Dict[str, Any]]:
    """
    Dynamically computes top substitution recommendations for a target ingredient using the Ingredient Ontology.
    """
    target = ingredient_name.lower().strip()
    ontology = get_ontology()

    ontology_subs = ontology.find_ontology_substitutes(
        target_ingredient=target,
        avoided_ingredients=avoided_ingredients,
        diet_preference=diet_preference,
        compatibility_graph=compatibility_graph,
        top_k=4
    )

    if ontology_subs:
        return ontology_subs

    # Generic Fallback if unknown ingredient
    return [{
        "original": target,
        "substitute": "Tofu / Soya Nuggets",
        "category_match": "plant_protein",
        "culinary_role": "protein_base / binder",
        "flavor_profile": "savory / neutral",
        "reasoning": "High-protein plant-based culinary structure substitute."
    }]

