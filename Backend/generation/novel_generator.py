import requests
from typing import List, Dict, Any, Optional
from core.schemas import QuerySpec
from generation.prompt_templates import build_novel_recipe_prompt, build_repair_prompt
from generation.output_parser import parse_recipe_json

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_ollama_raw(prompt: str, temperature: float = 0.6, num_predict: int = 750, timeout: float = 30.0) -> str:
    models_to_try = ["phi:latest", "gemma3:1b"]
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            if r.status_code == 200:
                resp = r.json().get("response", "").strip()
                if resp and len(resp) > 30:
                    return resp
        except Exception:
            continue
    return ""


def generate_novel_candidates(
    query_spec: QuerySpec,
    parent_recipes: List[Dict[str, Any]],
    compatible_ingredients: List[str],
    num_candidates: int = 3
) -> List[Dict[str, Any]]:
    """
    Generates 3-5 grounded novel recipe candidates using Ollama with temperature ~0.6 and num_predict >= 700.
    Applies 1-shot repair if output parsing fails, and falls back to ontology-grounded synthesis if Ollama is offline or slow.
    """
    prompt = build_novel_recipe_prompt(query_spec, parent_recipes, compatible_ingredients)
    candidates = []

    for idx in range(num_candidates):
        # Slightly alter temperature for candidate diversity across calls
        temp = 0.55 + (idx * 0.1)
        raw_resp = call_ollama_raw(prompt, temperature=temp, num_predict=750, timeout=30.0)

        if not raw_resp:
            if idx == 0:
                break  # Fast fallback to ontology candidate if Ollama is offline or slow
            continue

        parsed = parse_recipe_json(raw_resp)

        # 1-Shot Repair Request if parsing failed
        if not parsed:
            repair_p = build_repair_prompt(raw_resp, "Invalid JSON structure or missing mandatory fields")
            repaired_resp = call_ollama_raw(repair_p, temperature=0.2, num_predict=750, timeout=30.0)
            if repaired_resp:
                parsed = parse_recipe_json(repaired_resp)
                if parsed:
                    parsed["repaired"] = True

        if parsed:
            parsed["candidate_index"] = idx
            parsed["raw_response"] = raw_resp
            candidates.append(parsed)

    # Grounded Synthesis Fallback if Ollama is offline or slow
    if not candidates:
        fallback_recipe = _build_ontology_fallback_candidate(query_spec, parent_recipes, compatible_ingredients)
        if fallback_recipe:
            candidates.append(fallback_recipe)

    return candidates


def _build_ontology_fallback_candidate(
    query_spec: QuerySpec,
    parent_recipes: List[Dict[str, Any]],
    compatible_ingredients: List[str]
) -> Dict[str, Any]:
    """
    Generates an ontology-grounded structured culinary recipe candidate
    customized dynamically for the target dish type (Smoothie/Dessert, Soup, Salad, Breakfast, or Savory Main).
    """
    from ingredients.ontology import IngredientOntology
    ontology = IngredientOntology()

    req_ings = list(query_spec.ingredients_to_include) if query_spec.ingredients_to_include else []
    avoid_set = set([a.lower() for a in query_spec.ingredients_to_avoid])
    parent_id = parent_recipes[0].get("recipe_id", 1) if parent_recipes else 1

    q_text = (query_spec.original_query + " " + " ".join(req_ings) + " " + (query_spec.meal or "")).lower()

    # Category Keywords
    sweet_kw = ["smoothie", "smotthie", "shake", "milkshake", "juice", "drink", "beverage", "sweet", "dessert", "cake", "cookie", "pudding", "ice cream", "chocolate", "vanilla", "date", "dates", "peanut butter", "peenut butter", "strawberry", "banana", "apple", "blueberry", "mango", "berry", "honey", "sugar", "maple", "syrup", "milk", "oat", "yogurt", "curd", "cocoa", "cacao", "nutella"]
    soup_kw = ["soup", "broth", "stew", "ramen", "chowder"]
    salad_kw = ["salad", "bowl", "greens", "vinaigrette"]
    bfast_kw = ["pancake", "waffle", "oatmeal", "porridge", "toast", "omelette"]

    if any(k in q_text for k in sweet_kw):
        dish_cat = "sweet"
    elif any(k in q_text for k in soup_kw):
        dish_cat = "soup"
    elif any(k in q_text for k in salad_kw):
        dish_cat = "salad"
    elif any(k in q_text for k in bfast_kw):
        dish_cat = "breakfast"
    else:
        dish_cat = "savory"

    formatted_ings = []
    seen = set()

    def add_ingredient(name: str, amount: str, unit: str, role: str):
        norm = name.lower().strip()
        if norm in seen:
            return
        for av in avoid_set:
            if av in norm or norm in av:
                return
        seen.add(norm)
        formatted_ings.append({
            "name": name,
            "amount": amount,
            "unit": unit,
            "role": role,
            "supported_by": [parent_id]
        })

    # Add mandatory required ingredients
    for ing in req_ings:
        info = ontology.get_ingredient_info(ing)
        role = ", ".join(info.culinary_roles) if (info and info.culinary_roles) else "primary element"
        
        ing_l = ing.lower()
        if any(f in ing_l for f in ["oil", "ghee", "butter"]):
            amt, unit = "1.5", "tbsp"
        elif any(p in ing_l for p in ["chicken", "beef", "mutton", "lamb", "fish", "prawn"]):
            amt, unit = "250", "g"
        elif any(p in ing_l for p in ["paneer", "tofu", "cheese"]):
            amt, unit = "150", "g"
        elif any(l in ing_l for l in ["milk", "curd", "yogurt", "cream", "juice"]):
            amt, unit = "3", "tbsp" if dish_cat == "savory" else "1", "cup"
        else:
            amt, unit = "1", "item"
        add_ingredient(ing, amt, unit, role)

    if dish_cat == "sweet":
        sweet_staples = [
            ("milk", "1", "cup", "beverage liquid"),
            ("honey", "1", "tbsp", "sweetener"),
            ("vanilla extract", "1/2", "tsp", "flavor enhancer"),
            ("cocoa powder", "2", "tbsp", "primary flavor"),
            ("ice cubes", "4", "cubes", "chiller"),
            ("fresh mint", "2", "leaves", "garnish")
        ]
        for name, amt, unit, role in sweet_staples:
            add_ingredient(name, amt, unit, role)

        title_parts = [i["name"].title() for i in formatted_ings if i["name"].lower() in [r.lower() for r in req_ings]]
        if not title_parts:
            title_parts = ["Chocolate", "Peanut Butter"]
        
        if "smoothie" in q_text or "smotthie" in q_text or "shake" in q_text:
            title = f"Creamy {' '.join(title_parts)} Smoothie"
        else:
            title = f"Delicious {' '.join(title_parts)} Delight"

        all_names = ", ".join([i["name"] for i in formatted_ings])
        steps = [
            {
                "step": 1,
                "text": f"Add {all_names} into a high-speed blender container.",
                "supported_by": [parent_id]
            },
            {
                "step": 2,
                "text": "Blend on high speed for 60 seconds until completely smooth, thick, and creamy.",
                "supported_by": [parent_id]
            },
            {
                "step": 3,
                "text": "Pour into tall chilled glasses and garnish before serving immediately.",
                "supported_by": [parent_id]
            }
        ]

    elif dish_cat == "soup":
        soup_staples = [
            ("vegetable broth", "2", "cups", "liquid base"),
            ("olive oil", "1", "tbsp", "fat source"),
            ("onion", "1", "medium, chopped", "aromatic base"),
            ("black pepper", "1/2", "tsp", "seasoning"),
            ("salt", "to taste", "", "seasoning"),
            ("fresh parsley", "1", "tbsp", "garnish")
        ]
        for name, amt, unit, role in soup_staples:
            add_ingredient(name, amt, unit, role)

        main_solids = [i["name"] for i in formatted_ings if any(r.lower() in i["name"].lower() for r in req_ings)]
        title = f"Warm {' '.join([p.title() for p in main_solids])} Soup" if main_solids else "Comforting Vegetable Soup"
        
        combo = " and ".join(main_solids) if main_solids else "vegetables"
        steps = [
            {
                "step": 1,
                "text": f"Heat olive oil in a soup pot. Sauté onion and {combo} for 5 minutes until tender.",
                "supported_by": [parent_id]
            },
            {
                "step": 2,
                "text": "Pour in vegetable broth, season with salt and black pepper, and bring to a gentle simmer for 15 minutes.",
                "supported_by": [parent_id]
            },
            {
                "step": 3,
                "text": "Ladle into warm soup bowls and garnish with fresh parsley before serving.",
                "supported_by": [parent_id]
            }
        ]

    elif dish_cat == "salad":
        salad_staples = [
            ("mixed greens", "2", "cups", "base greens"),
            ("olive oil", "2", "tbsp", "dressing base"),
            ("lemon juice", "1", "tbsp", "acid enhancer"),
            ("black pepper", "1/2", "tsp", "seasoning"),
            ("salt", "to taste", "", "seasoning")
        ]
        for name, amt, unit, role in salad_staples:
            add_ingredient(name, amt, unit, role)

        main_solids = [i["name"] for i in formatted_ings if any(r.lower() in i["name"].lower() for r in req_ings)]
        title = f"Fresh {' '.join([p.title() for p in main_solids])} Salad" if main_solids else "Garden Salad"
        
        combo = " and ".join(main_solids) if main_solids else "ingredients"
        steps = [
            {
                "step": 1,
                "text": f"Wash and chop mixed greens, {combo} into bite-sized pieces.",
                "supported_by": [parent_id]
            },
            {
                "step": 2,
                "text": "Whisk olive oil, lemon juice, salt, and black pepper together in a small bowl for the dressing.",
                "supported_by": [parent_id]
            },
            {
                "step": 3,
                "text": f"Toss mixed greens and {combo} with the dressing and serve fresh.",
                "supported_by": [parent_id]
            }
        ]

    else:
        # Savory Main / Curry / Skillet
        savory_staples = [
            ("thick curd", "3", "tbsp", "marinade base"),
            ("olive oil", "1.5", "tbsp", "fat source"),
            ("onion", "1", "medium, chopped", "aromatic base"),
            ("tomato purée", "2", "medium, puréed", "sauce base"),
            ("cashews", "8-10", "soaked", "thickener"),
            ("ginger paste", "1", "tsp", "aromatic spice"),
            ("Kashmiri red chilli powder", "1", "tsp", "spice"),
            ("turmeric", "1/2", "tsp", "spice"),
            ("cumin powder", "1/2", "tsp", "spice"),
            ("coriander powder", "1/2", "tsp", "spice"),
            ("garam masala", "1/2", "tsp", "finishing spice"),
            ("kasuri methi", "1/2", "tsp", "herb flavor"),
            ("lemon juice", "1", "tsp", "acid enhancer"),
            ("cumin seeds", "1/2", "tsp", "whole spice"),
            ("salt", "to taste", "", "seasoning"),
            ("fresh coriander", "2", "tbsp", "garnish")
        ]
        for name, amt, unit, role in savory_staples:
            add_ingredient(name, amt, unit, role)

        spice_kw = ["asafoetida", "hing", "asafetida", "spice", "herb", "powder", "seed", "masala", "salt", "pepper", "turmeric", "chilli", "chili", "cumin", "coriander", "ginger", "garlic", "kasuri", "curd", "onion", "tomato", "cashew", "lemon"]
        main_solids = [
            i["name"] for i in formatted_ings 
            if any(r.lower() in i["name"].lower() for r in req_ings) 
            and not any(f in i["name"].lower() for f in ["oil", "ghee", "butter", "sauce", "powder", "salt", "juice", "purée", "water", "seed"] + spice_kw)
        ]
        
        if not main_solids:
            # If query only specified spices like asafoetida/hing, add potato as primary solid base
            add_ingredient("potato", "2", "medium, cubed", "primary vegetable base")
            main_solids = ["potato"]

        main_p1 = main_solids[0]
        main_p2 = main_solids[1] if len(main_solids) > 1 else None
        fat_item = next((i["name"] for i in formatted_ings if any(f in i["name"].lower() for f in ["oil", "ghee", "butter"])), "olive oil")

        title_parts = " ".join([p.title() for p in main_solids])
        title = f"Smoky {title_parts} Skillet" if title_parts else "Grounded Savory Skillet"

        combo = " and ".join(main_solids) if len(main_solids) <= 2 else ", ".join(main_solids[:-1]) + ", and " + main_solids[-1]

        # Check if asafoetida/hing is in required ingredients
        has_asa = any("asafoetida" in i["name"].lower() or "hing" in i["name"].lower() for i in formatted_ings)
        asa_str = ", a pinch of asafoetida (hing)," if has_asa else ""

        steps = [
            {
                "step": 1,
                "text": f"Mix {combo} with thick curd, ginger paste, Kashmiri red chilli powder, turmeric, cumin powder, lemon juice, and salt in a bowl. Marinate for 20–30 minutes.",
                "supported_by": [parent_id]
            },
            {
                "step": 2,
                "text": f"Heat 1 tsp {fat_item} in a skillet over medium-high heat. Cook the {main_p1} until browned and nearly cooked through. Remove and set aside.",
                "supported_by": [parent_id]
            }
        ]

        if main_p2:
            steps.append({
                "step": len(steps) + 1,
                "text": f"Sear the {main_p2} in the same skillet until golden brown. Remove and set aside.",
                "supported_by": [parent_id]
            })

        for extra in main_solids[2:]:
            steps.append({
                "step": len(steps) + 1,
                "text": f"Sauté the {extra} briefly in the skillet until fragrant. Remove and set aside.",
                "supported_by": [parent_id]
            })

        steps.extend([
            {
                "step": len(steps) + 1,
                "text": f"Add the remaining {fat_item}, cumin seeds{asa_str} to the skillet. Add onion and cook until golden brown.",
                "supported_by": [parent_id]
            },
            {
                "step": len(steps) + 1,
                "text": "Add tomato purée, coriander powder, Kashmiri red chilli powder, and salt. Cook for 5–7 minutes until sauce thickens.",
                "supported_by": [parent_id]
            },
            {
                "step": len(steps) + 1,
                "text": "Blend the soaked cashews with a little water into a paste and add to the skillet. Simmer for 2–3 minutes.",
                "supported_by": [parent_id]
            },
            {
                "step": len(steps) + 1,
                "text": f"Return the {combo} to the skillet. Sprinkle with garam masala and kasuri methi.",
                "supported_by": [parent_id]
            },
            {
                "step": len(steps) + 1,
                "text": f"Cover and cook for 3–4 minutes until the {combo} is fully cooked and the sauce thickens.",
                "supported_by": [parent_id]
            },
            {
                "step": len(steps) + 1,
                "text": "Garnish with fresh coriander and a squeeze of lemon juice before serving hot.",
                "supported_by": [parent_id]
            }
        ])

    for idx, st in enumerate(steps, 1):
        st["step"] = idx

    return {
        "title": title,
        "servings": 2,
        "prep_time": 10,
        "cook_time": 20 if dish_cat == "savory" else 0,
        "ingredients": formatted_ings,
        "instructions": steps,
        "candidate_index": 0,
        "raw_response": "Grounded Ontology Fallback Candidate",
        "grounded_fallback": True
    }

