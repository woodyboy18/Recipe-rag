"""
Evaluation Prompts and Rubrics for G-Eval-Inspired LLM-as-a-Judge Framework
Strictly adheres to:
"G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment" (Liu et al., 2023)

Four Final Evaluation Metrics:
1. Correctness (0.0 - 1.0)
2. Faithfulness (0.0 - 1.0)
3. Hallucination-Free Score (0.0 - 1.0)
4. Constraint Adherence (0.0 - 1.0)
"""

from typing import Dict, Any, List

# ==============================================================================
# G-EVAL EVALUATION STEPS & CRITERIA
# ==============================================================================

GEVAL_METRIC_DEFINITIONS = {
    "correctness": {
        "name": "Correctness",
        "description": "Evaluate the factual, culinary, and technical correctness of the generated recipe.",
        "criteria": (
            "Determine whether the recipe is technically sound, feasible to prepare, and logically consistent. "
            "Verify that ingredient proportions are culinarily viable, cooking temperatures and durations are "
            "realistic, preparation sequences follow proper thermodynamic stages (e.g., aromatics tempered before "
            "liquids are added), and that instructions do not contain self-contradictory steps."
        ),
        "evaluation_steps": [
            "1. Analyze ingredient quantities and units to verify they yield a realistic, edible dish with appropriate proportions.",
            "2. Examine cooking steps sequentially to verify chronological and thermodynamic soundness (e.g., blooming spices, searing, simmering).",
            "3. Verify that cooking temperatures, heat levels (low, medium, high), and timings are realistic and food-safe.",
            "4. Check for internal contradictions between the ingredient list and the instructions (e.g., ingredients mentioned in instructions but omitted from list, or vice versa).",
            "5. Assess overall procedural feasibility: could an ordinary cook follow these instructions to produce the stated dish successfully?"
        ],
        "rubric": {
            1: "Extremely poor (0.0-0.19): Incoherent, hazardous, or physically impossible cooking instructions; severely absurd ingredient ratios.",
            2: "Poor (0.20-0.39): Major procedural errors, impossible timings, missing essential preparation steps, or strong self-contradictions.",
            3: "Moderate (0.40-0.59): Cookable with significant improvisation; noticeable discrepancies in ingredient ratios or vague cooking steps.",
            4: "Good (0.60-0.79): Technically sound with minor flaws (e.g., slightly high seasoning, minor step order optimization needed).",
            5: "Excellent (0.80-1.00): Flawless culinary logic, precise proportions, completely consistent instructions, and thermodynamically sound steps."
        }
    },
    "faithfulness": {
        "name": "Faithfulness",
        "description": "Evaluate whether the generated recipe is appropriately grounded in the retrieved recipe context.",
        "criteria": (
            "Determine whether the generated recipe appropriately leverages culinary motifs, flavor bases, and "
            "techniques from the retrieved evidence recipes without directly copying or misrepresenting them. "
            "IMPORTANT: Novel recipe generation inherently involves creative synthesis and modifications; "
            "do NOT penalize the recipe simply for introducing compatible new ingredients or innovative combinations. "
            "Penalize only if the generated recipe distorts, contradicts, or falsely claims alignment with the retrieved context."
        ),
        "evaluation_steps": [
            "1. Identify key culinary elements in the retrieved evidence recipes (core flavor profiles, cooking techniques, sauce bases).",
            "2. Compare the generated recipe against the retrieved evidence to verify that retrieved culinary foundations are meaningfully utilized.",
            "3. Distinguish between legitimate creative transformations (e.g., substituting paneer into a skillet stir-fry) versus unsupported contradictions.",
            "4. Check whether the recipe misrepresents or distorts the techniques demonstrated in the parent recipes.",
            "5. Assess whether the recipe exhibits genuine contextual grounding rather than ignoring the retrieved knowledge entirely."
        ],
        "rubric": {
            1: "Extremely poor (0.0-0.19): Entirely ungrounded; contradicts retrieved evidence or ignores retrieved context completely.",
            2: "Poor (0.20-0.39): Weak or distorted connection to retrieved recipes; misapplies techniques found in the evidence.",
            3: "Moderate (0.40-0.59): Partial grounding; borrows superficial elements from evidence but misses structural techniques.",
            4: "Good (0.60-0.79): Well grounded; appropriately adapts techniques and ingredients from parent recipes with sound modifications.",
            5: "Excellent (0.80-1.00): Exemplary contextual grounding; seamlessly transforms parent motifs into a coherent novel dish without copying."
        }
    },
    "hallucination": {
        "name": "Hallucination-Free Score",
        "description": "Evaluate the absence of fabricated facts, impossible properties, or contradictory claims.",
        "criteria": (
            "Evaluate whether the generated recipe contains unsupported, fabricated, contradictory, or factually "
            "incorrect information. This is a HALLUCINATION-FREE score where 1.0 means completely hallucination-free "
            "and 0.0 means severe hallucinations. "
            "IMPORTANT: Do not treat novel culinary combinations as hallucinations. A hallucination is a false factual "
            "claim (e.g., claiming cumin contains 50g protein per tsp, claiming water boils at 50C, or inventing non-existent ingredients)."
        ),
        "evaluation_steps": [
            "1. Scan the ingredient list for fabricated, non-existent ingredients or false culinary entities.",
            "2. Scrutinize factual assertions regarding ingredient properties (e.g., claiming a spice is a primary bulk protein source).",
            "3. Check for physical or chemical impossibilities (e.g., claiming oil dissolves water, melting solids without heat).",
            "4. Verify that preparation timings and yield claims are factually plausible and not fabricated.",
            "5. Differentiate carefully between novel creative pairings (valid) and objectively false claims (hallucination)."
        ],
        "rubric": {
            1: "Extremely poor (0.0-0.19): Severe hallucinations; fabricated ingredients, impossible physical transformations, absurd nutritional assertions.",
            2: "Poor (0.20-0.39): Multiple notable hallucinations; false culinary properties and distorted physical claims.",
            3: "Moderate (0.40-0.59): Moderate hallucinations; minor fabricated properties or unrealistic yield/time claims.",
            4: "Good (0.60-0.79): Largely hallucination-free; at most trivial, harmless exaggerations that do not compromise the recipe.",
            5: "Excellent (0.80-1.00): Completely hallucination-free; 100% of claims, ingredients, and instructions are factually sound."
        }
    },
    "constraint_adherence": {
        "name": "Constraint Adherence",
        "description": "Evaluate whether the generated recipe satisfies all explicitly stated user constraints.",
        "criteria": (
            "Determine whether the generated recipe fulfills the explicit requirements in the user query, including "
            "dietary preferences (vegan, vegetarian, keto), forbidden/excluded ingredients (e.g., no eggs, no garlic), "
            "mandatory included ingredients, meal type, and preparation time limits. "
            "IMPORTANT: Hard dietary and allergen exclusions are strictly binary violations. If a user asks for 'no eggs' "
            "and egg whites or mayonnaise appear, the score must be heavily penalized. Do not invent non-stated constraints."
        ),
        "evaluation_steps": [
            "1. Extract all explicit constraints from the user query: mandatory ingredients, excluded ingredients, dietary regimen, meal type, time limit.",
            "2. Check mandatory ingredients: are all requested ingredients present in the recipe?",
            "3. Check excluded ingredients (CRITICAL): does the recipe contain ANY forbidden ingredients, direct derivatives, or hidden aliases?",
            "4. Check dietary regimen & meal type: does the dish conform to the requested category (e.g., vegetarian, breakfast)?",
            "5. Check time constraints: are the total preparation and cooking times within the specified limit?",
            "6. Deduct severely for hard exclusion violations; do not penalize for constraints the user did not specify."
        ],
        "rubric": {
            1: "Extremely poor (0.0-0.19): Total disregard for constraints; violates core dietary/allergen exclusion, misses all requested items.",
            2: "Poor (0.20-0.39): Violates an explicit exclusion (e.g., includes dairy in a vegan request) or misses multiple mandatory ingredients.",
            3: "Moderate (0.40-0.59): Complies with exclusions but misses a key mandatory ingredient, or significantly exceeds time limits.",
            4: "Good (0.60-0.79): Satisfies all hard exclusions and mandatory ingredients, with minor deviation in secondary constraints (e.g., slightly over time).",
            5: "Excellent (0.80-1.00): Flawlessly adheres to every explicit constraint: all mandatory present, zero excluded, perfect dietary and time compliance."
        }
    }
}

# ==============================================================================
# PROMPT FORMATTERS
# ==============================================================================

def format_recipe_for_prompt(recipe_obj: Any) -> str:
    """Formats a recipe (dict or object) into a clear textual representation."""
    if isinstance(recipe_obj, dict):
        title = recipe_obj.get("title", "Untitled Novel Recipe")
        servings = recipe_obj.get("servings", "N/A")
        prep_time = recipe_obj.get("prep_time", "N/A")
        cook_time = recipe_obj.get("cook_time", "N/A")
        
        ingredients = recipe_obj.get("ingredients", [])
        if isinstance(ingredients, list):
            ing_lines = []
            for item in ingredients:
                if isinstance(item, dict):
                    qty = f"{item.get('amount', '')} {item.get('unit', '')}".strip()
                    ing_lines.append(f"- {qty} {item.get('name', '')}".strip())
                else:
                    ing_lines.append(f"- {str(item)}")
            ings_str = "\n".join(ing_lines)
        else:
            ings_str = str(ingredients)
            
        instructions = recipe_obj.get("instructions", [])
        if isinstance(instructions, list):
            inst_lines = [f"{i+1}. {step}" for i, step in enumerate(instructions)]
            inst_str = "\n".join(inst_lines)
        else:
            inst_str = str(instructions)
            
        return (
            f"Title: {title}\n"
            f"Servings: {servings} | Prep Time: {prep_time} mins | Cook Time: {cook_time} mins\n\n"
            f"Ingredients:\n{ings_str}\n\n"
            f"Instructions:\n{inst_str}"
        )
    return str(recipe_obj)


def format_retrieved_recipes_for_prompt(retrieved_recipes: List[Any], max_parents: int = 4) -> str:
    """Formats retrieved parent recipes into structured evidence blocks."""
    if not retrieved_recipes:
        return "No retrieved evidence recipes provided."
        
    formatted_parents = []
    for idx, rec in enumerate(retrieved_recipes[:max_parents], 1):
        if isinstance(rec, dict):
            p_title = rec.get("title", f"Evidence Recipe {idx}")
            p_ings = rec.get("ingredients", "")
            if isinstance(p_ings, list):
                p_ings = ", ".join([str(i) for i in p_ings[:15]])
            p_inst = rec.get("instructions", "")
            if isinstance(p_inst, list):
                p_inst = " ".join([str(s) for s in p_inst[:3]])
            p_inst = str(p_inst)[:300]
            
            formatted_parents.append(
                f"[Evidence Recipe {idx}]: {p_title}\n"
                f"  Ingredients: {p_ings}\n"
                f"  Instructions summary: {p_inst}..."
            )
        else:
            formatted_parents.append(f"[Evidence Recipe {idx}]: {str(rec)[:300]}")
            
    return "\n\n".join(formatted_parents)


# ==============================================================================
# SINGLE-METRIC G-EVAL PROMPT BUILDER (FOR STRICT LOGPROB EXPECTATION)
# ==============================================================================

def build_single_metric_geval_prompt(
    metric_key: str,
    user_query: str,
    retrieved_recipes: List[Any],
    generated_recipe: Any
) -> str:
    """
    Constructs a single-metric G-Eval prompt adhering strictly to Liu et al. (2023).
    Includes criteria, explicit CoT evaluation steps, form-filling inputs,
    and a final scoring trigger token for logprob extraction.
    """
    metric_info = GEVAL_METRIC_DEFINITIONS.get(metric_key)
    if not metric_info:
        raise ValueError(f"Unknown metric key: {metric_key}. Valid: {list(GEVAL_METRIC_DEFINITIONS.keys())}")
        
    steps_str = "\n".join(metric_info["evaluation_steps"])
    rubric_lines = [f"- Rating {score}: {desc}" for score, desc in metric_info["rubric"].items()]
    rubric_str = "\n".join(rubric_lines)
    
    recipe_str = format_recipe_for_prompt(generated_recipe)
    context_str = format_retrieved_recipes_for_prompt(retrieved_recipes)
    
    prompt = f"""You are an expert culinary scientist and NLG evaluation judge.
Your task is to evaluate a generated novel recipe based on a specific evaluation dimension following the G-Eval protocol.

EVALUATION METRIC: {metric_info['name']}
DESCRIPTION: {metric_info['description']}

CRITERIA:
{metric_info['criteria']}

EVALUATION STEPS:
{steps_str}

SCORING RUBRIC (Scale of 1 to 5):
{rubric_str}

--------------------------------------------------
USER QUERY & CONSTRAINTS:
{user_query}

RETRIEVED CONTEXT (Evidence Recipes from RecipeDB):
{context_str}

GENERATED NOVEL RECIPE TO EVALUATE:
{recipe_str}
--------------------------------------------------

INSTRUCTIONS:
1. Carry out the evaluation steps sequentially. Provide detailed chain-of-thought analysis citing explicit evidence from the query, context, and generated recipe.
2. Clearly list any identified issues, errors, or constraint violations.
3. Conclude by rating the recipe with an integer score from 1 to 5, where 1 is the worst and 5 is the best, strictly matching the rubric.

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
Analysis:
<Detailed step-by-step reasoning following each evaluation step>

Evidence:
- <Specific quoted evidence 1>
- <Specific quoted evidence 2>

Issues:
- <Specific issue or violation, or 'None' if completely sound>

Score: [Score]
(Note: Replace [Score] with a single integer between 1 and 5)
"""
    return prompt.strip()


# ==============================================================================
# UNIFIED MULTI-METRIC G-EVAL PROMPT (JSON FORMAT FOR BATCH RUNS)
# ==============================================================================

def build_unified_geval_prompt(
    user_query: str,
    retrieved_recipes: List[Any],
    generated_recipe: Any
) -> str:
    """
    Unified evaluation prompt evaluating all four metrics in a single pass
    while preserving individual criteria, CoT steps, and producing valid JSON.
    Used for cost-efficient batch runs or when logprobs are mapped across metrics.
    """
    recipe_str = format_recipe_for_prompt(generated_recipe)
    context_str = format_retrieved_recipes_for_prompt(retrieved_recipes)
    
    prompt = f"""You are an expert computational gastronomy and NLG evaluation judge.
Evaluate the following generated novel recipe against the user query and retrieved context using the G-Eval evaluation framework.

Evaluate strictly across these FOUR dimensions (scores must be continuous floating-point values between 0.0 and 1.0):

1. CORRECTNESS: Technical and culinary soundness, realistic ingredient proportions, chronological & thermodynamic step logic, absence of internal contradictions. (0.0 = completely broken/hazardous, 1.0 = flawless culinary logic)
2. FAITHFULNESS: Grounded in retrieved evidence without copying. Do NOT penalize for novel combinations or creative modifications. Penalize only for contradicting or distorting evidence. (0.0 = completely ungrounded/contradictory, 1.0 = seamless contextual transformation)
3. HALLUCINATION (Hallucination-free score): Absence of fabricated ingredients, impossible physics/chemistry, or absurd nutritional assertions. Creative recipe innovation is NOT hallucination. (0.0 = severe hallucinations, 1.0 = completely hallucination-free)
4. CONSTRAINT ADHERENCE: Compliance with all explicit user requirements (dietary restrictions, forbidden ingredients, inclusions, time, meal type). Hard allergen/dietary violations must receive zero. (0.0 = severe violation, 1.0 = perfect compliance)

OVERALL SCORE: Arithmetic mean = (Correctness + Faithfulness + Hallucination + Constraint Adherence) / 4.

--------------------------------------------------
USER QUERY:
{user_query}

RETRIEVED RECIPES (Parent Evidence from RecipeDB):
{context_str}

GENERATED NOVEL RECIPE:
{recipe_str}
--------------------------------------------------

Respond ONLY with valid, parseable JSON matching this schema:
{{
  "correctness": {{
    "score": <float between 0.0 and 1.0>,
    "reason": "<Detailed step-by-step reasoning>",
    "evidence": ["<quoted evidence 1>", "<quoted evidence 2>"],
    "issues": ["<specific issue or empty list>"]
  }},
  "faithfulness": {{
    "score": <float between 0.0 and 1.0>,
    "reason": "<Detailed step-by-step reasoning>",
    "evidence": ["<quoted evidence 1>"],
    "issues": []
  }},
  "hallucination": {{
    "score": <float between 0.0 and 1.0>,
    "reason": "<Detailed step-by-step reasoning>",
    "evidence": ["<quoted evidence 1>"],
    "issues": []
  }},
  "constraint_adherence": {{
    "score": <float between 0.0 and 1.0>,
    "reason": "<Detailed step-by-step reasoning>",
    "evidence": ["<quoted evidence 1>"],
    "issues": []
  }},
  "overall_score": <float arithmetic mean between 0.0 and 1.0>
}}
"""
    return prompt.strip()
