"""
Ingredient Ontology Module
Provides class-based culinary taxonomy reasoning over ingredient categories,
culinary functional roles, flavor profiles, and taste-preserving substitutions.
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list

DATA_PATH = os.path.join(os.path.dirname(__file__), "ontology_data.json")


@dataclass
class IngredientNode:
    canonical_name: str
    category: str = "general"
    culinary_roles: List[str] = field(default_factory=list)
    flavor_profiles: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    substitutes: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_name": self.canonical_name,
            "category": self.category,
            "culinary_roles": self.culinary_roles,
            "flavor_profiles": self.flavor_profiles,
            "synonyms": self.synonyms,
            "substitutes": self.substitutes
        }


class IngredientOntology:
    """
    Class-based Ingredient Ontology Taxonomy Manager.
    Loads taxonomy data and performs function-aware and taste-preserving substitutions.
    """

    def __init__(self, json_path: str = DATA_PATH):
        self.nodes: Dict[str, IngredientNode] = {}
        self.synonym_map: Dict[str, str] = {}
        self.categories: Dict[str, List[str]] = {}
        self.culinary_roles: Dict[str, List[str]] = {}
        self.flavor_profiles: Dict[str, List[str]] = {}
        self.load_ontology(json_path)

    def load_ontology(self, json_path: str):
        if not os.path.exists(json_path):
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.categories = data.get("categories", {})
        self.culinary_roles = data.get("culinary_roles", {})
        self.flavor_profiles = data.get("flavor_profiles", {})
        synonyms_dict = data.get("synonyms", {})
        substitutions_dict = data.get("substitutions", {})

        # Build Synonym Map
        for canonical, syns in synonyms_dict.items():
            norm_canon = normalize_ingredient(canonical)
            self.synonym_map[norm_canon] = norm_canon
            for s in syns:
                norm_s = normalize_ingredient(s)
                if norm_s:
                    self.synonym_map[norm_s] = norm_canon

        # Gather all unique ingredient names across categories
        all_ings: Set[str] = set()
        for cat_list in self.categories.values():
            for ing in cat_list:
                all_ings.add(normalize_ingredient(ing))

        for ing in all_ings:
            if not ing:
                continue

            canon = self.resolve_canonical(ing)

            # Determine category
            ing_cat = "general"
            for cat, items in self.categories.items():
                if any(normalize_ingredient(item) == canon for item in items):
                    ing_cat = cat
                    break

            # Determine culinary roles
            roles = []
            for role, items in self.culinary_roles.items():
                if any(normalize_ingredient(item) == canon for item in items):
                    roles.append(role)

            # Determine flavor profiles
            flavors = []
            for flavor, items in self.flavor_profiles.items():
                if any(normalize_ingredient(item) == canon for item in items):
                    flavors.append(flavor)

            # Synonyms & Substitutes
            syns = synonyms_dict.get(canon, [])
            subs = substitutions_dict.get(canon, [])

            node = IngredientNode(
                canonical_name=canon,
                category=ing_cat,
                culinary_roles=roles,
                flavor_profiles=flavors,
                synonyms=syns,
                substitutes=subs
            )
            self.nodes[canon] = node

    def resolve_canonical(self, name: str) -> str:
        norm = normalize_ingredient(name)
        return self.synonym_map.get(norm, norm)

    def get_ingredient_info(self, name: str) -> Optional[IngredientNode]:
        canon = self.resolve_canonical(name)
        return self.nodes.get(canon)

    def get_category(self, name: str) -> str:
        node = self.get_ingredient_info(name)
        return node.category if node else "general"

    def get_culinary_roles(self, name: str) -> List[str]:
        node = self.get_ingredient_info(name)
        return node.culinary_roles if node else []

    def get_flavor_profiles(self, name: str) -> List[str]:
        node = self.get_ingredient_info(name)
        return node.flavor_profiles if node else []

    def find_ontology_substitutes(
        self,
        target_ingredient: str,
        avoided_ingredients: List[str] = None,
        diet_preference: str = None,
        compatibility_graph = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Dynamically finds substitutes matching the target ingredient's culinary roles and flavor profiles.
        Ranks candidates by role matching, flavor matching, and dataset co-occurrence compatibility.
        """
        target_norm = normalize_ingredient(target_ingredient)
        target_node = self.get_ingredient_info(target_norm)

        avoided_set = set(normalize_ingredient_list(avoided_ingredients or []))
        avoided_set.add(target_norm)

        results = []

        # 1. Direct Linked Substitutes in Ontology
        if target_node and target_node.substitutes:
            for sub in target_node.substitutes:
                sub_name = normalize_ingredient(sub.get("name", ""))
                if sub_name and sub_name not in avoided_set:
                    # Check diet restriction
                    if diet_preference in ["vegetarian", "vegan"] and self.get_category(sub_name) == "animal_protein":
                        continue
                    
                    sub_node = self.get_ingredient_info(sub_name)
                    results.append({
                        "original": target_norm,
                        "substitute": sub.get("name"),
                        "category_match": sub_node.category if sub_node else "general",
                        "culinary_role": sub.get("role", ", ".join(target_node.culinary_roles) if target_node else "substitute"),
                        "flavor_profile": sub.get("flavor", ", ".join(target_node.flavor_profiles) if target_node else "compatible flavor"),
                        "reasoning": sub.get("note", "Ontology functional role & flavor match.")
                    })

        # 2. Dynamic Taxonomy Matching (Role + Category + Taste)
        if len(results) < top_k and target_node:
            for cand_name, cand_node in self.nodes.items():
                if cand_name in avoided_set:
                    continue

                if any(r.get("substitute").lower() == cand_name for r in results):
                    continue

                # Filter by diet
                if diet_preference in ["vegetarian", "vegan"] and cand_node.category == "animal_protein":
                    continue

                # Check shared culinary role or flavor profile
                shared_roles = set(target_node.culinary_roles).intersection(cand_node.culinary_roles)
                shared_flavors = set(target_node.flavor_profiles).intersection(cand_node.flavor_profiles)

                if shared_roles or shared_flavors or cand_node.category == target_node.category:
                    comp_score = 0.5
                    if compatibility_graph:
                        comp_score = compatibility_graph.compatibility_score(target_norm, cand_name)

                    role_desc = ", ".join(shared_roles) if shared_roles else (", ".join(cand_node.culinary_roles) or "culinary equivalent")
                    flavor_desc = ", ".join(shared_flavors) if shared_flavors else (", ".join(cand_node.flavor_profiles) or "taste compatible")

                    results.append({
                        "original": target_norm,
                        "substitute": cand_node.canonical_name.title(),
                        "category_match": cand_node.category,
                        "culinary_role": role_desc,
                        "flavor_profile": flavor_desc,
                        "reasoning": f"Taxonomy match: shares {role_desc} role & {flavor_desc} profile."
                    })

        # 3. Graph Co-Occurrence Fallback if still under top_k
        if len(results) < top_k and compatibility_graph:
            comp_tuples = compatibility_graph.get_compatible(target_norm, top_n=8)
            for c_name, c_score in comp_tuples:
                if c_name not in avoided_set and not any(r.get("substitute").lower() == c_name for r in results):
                    if diet_preference in ["vegetarian", "vegan"] and self.get_category(c_name) == "animal_protein":
                        continue

                    c_node = self.get_ingredient_info(c_name)
                    results.append({
                        "original": target_norm,
                        "substitute": c_name.title(),
                        "category_match": c_node.category if c_node else "general",
                        "culinary_role": ", ".join(c_node.culinary_roles) if (c_node and c_node.culinary_roles) else "culinary pairing",
                        "flavor_profile": ", ".join(c_node.flavor_profiles) if (c_node and c_node.flavor_profiles) else "flavor pairing",
                        "reasoning": f"Dataset co-occurrence pair (PPMI score: {round(c_score, 2)})."
                    })

        return results[:top_k]
