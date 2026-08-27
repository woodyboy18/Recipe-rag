import json
import re
from typing import Dict, Any, Optional

def parse_recipe_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly parses JSON model output. Strips Markdown fences and validates required keys.
    Returns None if invalid (never returns fake fallback content).
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    clean = raw_text.strip()

    # Strip markdown code blocks ```json ... ``` or ``` ... ```
    if "```" in clean:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
        if match:
            clean = match.group(1).strip()
        else:
            clean = re.sub(r"^```[a-zA-Z]*\n?", "", clean)
            clean = re.sub(r"\n?```$", "", clean).strip()

    # Extract JSON object substring if surrounding conversational text exists
    if not (clean.startswith("{") and clean.endswith("}")):
        json_match = re.search(r"\{[\s\S]*\}", clean)
        if json_match:
            clean = json_match.group(0).strip()

    try:
        data = json.loads(clean)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    # Validate mandatory fields
    title = data.get("title")
    ingredients = data.get("ingredients")
    instructions = data.get("instructions")

    if not title or not isinstance(title, str) or len(title.strip()) < 2:
        return None

    if not ingredients or not isinstance(ingredients, list) or len(ingredients) == 0:
        return None

    if not instructions or not isinstance(instructions, list) or len(instructions) == 0:
        return None

    # Normalize ingredients format to standard dict list or string list
    normalized_ings = []
    for item in ingredients:
        if isinstance(item, dict):
            name = item.get("name", "").strip()
            amount = str(item.get("amount", "1")).strip()
            unit = str(item.get("unit", "")).strip()
            role = item.get("role", "")
            supp = item.get("supported_by", [])
            if name:
                normalized_ings.append({
                    "name": name,
                    "amount": amount,
                    "unit": unit,
                    "role": role,
                    "supported_by": supp,
                    "raw": f"{amount} {unit} {name}".strip()
                })
        elif isinstance(item, str) and item.strip():
            normalized_ings.append({
                "name": item.strip(),
                "amount": "1",
                "unit": "",
                "role": "",
                "supported_by": [],
                "raw": item.strip()
            })

    if not normalized_ings:
        return None

    # Normalize instructions format to list of strings and list of dicts
    normalized_insts = []
    inst_strings = []
    for i, step in enumerate(instructions, 1):
        if isinstance(step, dict):
            text = step.get("text", "").strip()
            supp = step.get("supported_by", [])
            if text:
                normalized_insts.append({"step": i, "text": text, "supported_by": supp})
                inst_strings.append(text)
        elif isinstance(step, str) and step.strip():
            normalized_insts.append({"step": i, "text": step.strip(), "supported_by": []})
            inst_strings.append(step.strip())

    if not inst_strings:
        return None

    return {
        "title": title.strip(),
        "servings": int(data.get("servings", 2)) if data.get("servings") else 2,
        "prep_time": int(data.get("prep_time", 10)) if data.get("prep_time") else 10,
        "cook_time": int(data.get("cook_time", 15)) if data.get("cook_time") else 15,
        "ingredients": normalized_ings,
        "instructions": inst_strings,
        "instructions_structured": normalized_insts,
        "raw_parsed": data
    }
