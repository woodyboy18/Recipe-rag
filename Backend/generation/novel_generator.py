import requests
from typing import List, Dict, Any, Optional
from core.schemas import QuerySpec
from generation.prompt_templates import build_novel_recipe_prompt, build_repair_prompt
from generation.output_parser import parse_recipe_json

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_ollama_raw(prompt: str, temperature: float = 0.6, num_predict: int = 750, timeout: int = 30) -> str:
    models_to_try = ["mistral:latest", "llama3:latest", "phi:latest"]
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
    Applies 1-shot repair if output parsing fails.
    """
    prompt = build_novel_recipe_prompt(query_spec, parent_recipes, compatible_ingredients)
    candidates = []

    for idx in range(num_candidates):
        # Slightly alter temperature for candidate diversity across calls
        temp = 0.55 + (idx * 0.1)
        raw_resp = call_ollama_raw(prompt, temperature=temp, num_predict=750)

        if not raw_resp:
            continue

        parsed = parse_recipe_json(raw_resp)

        # 1-Shot Repair Request if parsing failed
        if not parsed:
            repair_p = build_repair_prompt(raw_resp, "Invalid JSON structure or missing mandatory fields")
            repaired_resp = call_ollama_raw(repair_p, temperature=0.2, num_predict=750)
            if repaired_resp:
                parsed = parse_recipe_json(repaired_resp)
                if parsed:
                    parsed["repaired"] = True

        if parsed:
            parsed["candidate_index"] = idx
            parsed["raw_response"] = raw_resp
            candidates.append(parsed)

    return candidates
