from typing import List, Dict, Any
from core.schemas import QuerySpec

def build_novel_recipe_prompt(
    query_spec: QuerySpec,
    parent_recipes: List[Dict[str, Any]],
    compatible_ingredients: List[str]
) -> str:
    """
    Builds strict novel recipe synthesis prompt requiring JSON output grounded in parent evidence and compatibility graph.
    """
    parents_summary = []
    for i, p in enumerate(parent_recipes, 1):
        parents_summary.append(
            f"Evidence Recipe {i} [ID: {p.get('recipe_id')}]: {p.get('title')}\n"
            f"  Ingredients: {p.get('ingredients')}\n"
            f"  Instructions: {p.get('instructions')[:250]}..."
        )

    parents_str = "\n\n".join(parents_summary) if parents_summary else "No specific parent recipes available."
    req_str = ", ".join(query_spec.ingredients_to_include) if query_spec.ingredients_to_include else "None"
    avoid_str = ", ".join(query_spec.ingredients_to_avoid) if query_spec.ingredients_to_avoid else "None"
    comp_str = ", ".join(compatible_ingredients) if compatible_ingredients else "Standard culinary staples"

    prompt = f"""You are a grounded culinary recipe synthesis system.

Use the evidence recipes as culinary building blocks, but do not copy any complete recipe.

Create one coherent new recipe satisfying the user constraints.

Mandatory ingredients:
{req_str}

Forbidden ingredients:
{avoid_str}

Meal type:
{query_spec.meal or "Any"}

Diet:
{query_spec.diet or "Standard"}

Cuisine:
{query_spec.cuisine or "General"}

Evidence recipes:
{parents_str}

Compatible supporting ingredients:
{comp_str}

Rules:
1. Include every mandatory ingredient.
2. Exclude every forbidden ingredient.
3. Add a supporting ingredient only if it appears in an evidence recipe or compatibility graph.
4. Every ingredient must be used in at least one instruction.
5. Every ingredient mentioned in an instruction must be present in the ingredient list.
6. Produce realistic quantities, units and ordered cooking steps.
7. Create a new ingredient combination or cooking structure rather than copying one source.
8. Return valid JSON only.
9. Do not include Markdown code fences.

Required JSON format:
{{
  "title": "<Recipe Title>",
  "servings": 2,
  "prep_time": 10,
  "cook_time": 20,
  "ingredients": [
    {{
      "name": "strawberry",
      "amount": "1",
      "unit": "cup",
      "role": "primary flavour",
      "supported_by": ["recipe_id"]
    }}
  ],
  "instructions": [
    {{
      "step": 1,
      "text": "<Step instruction>",
      "supported_by": ["recipe_id"]
    }}
  ]
}}
"""
    return prompt


def build_repair_prompt(invalid_output: str, error_msg: str) -> str:
    return f"""The previous JSON recipe generation failed validation with this error: {error_msg}

Invalid raw response was:
{invalid_output[:400]}

Please correct the JSON output now. Return ONLY valid JSON matching the required structure without Markdown code blocks or explanation.
"""
