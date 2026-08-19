"""
Dynamic Prompt Builder & Prompt Selector Module
Constructs intent-specific system prompts based on detected Intent and ExecutionPlan.
Enforces zero-hallucination, structured JSON output formatting, and context retention.
"""

from state.recipe_state import RecipeState
from memory.memory_manager import UserPreferences

def build_prompt(
    intent: str,
    query: str,
    active_recipe: RecipeState = None,
    retrieved_context: str = "",
    user_prefs: UserPreferences = None
) -> str:
    """
    Synthesizes an intent-tailored prompt for local Ollama SLMs.
    """
    pref_str = ""
    if user_prefs:
        p_items = []
        if user_prefs.dietary_preference:
            p_items.append(f"Diet: {user_prefs.dietary_preference}")
        if user_prefs.allergies:
            p_items.append(f"Allergies to avoid: {', '.join(user_prefs.allergies)}")
        if user_prefs.disliked_ingredients:
            p_items.append(f"Disliked ingredients: {', '.join(user_prefs.disliked_ingredients)}")
        if p_items:
            pref_str = "User Profile & Dietary Preferences: " + " | ".join(p_items)

    recipe_ctx = ""
    if active_recipe:
        recipe_ctx = f"""
Active Current Recipe:
Title: {active_recipe.title}
Ingredients: {', '.join([ing.name for ing in active_recipe.ingredients])}
Instructions: {'; '.join(active_recipe.instructions[:3])}...
Servings: {active_recipe.servings}
"""

    if intent == "GENERAL_CHAT":
        return f"""
You are Chef AI, an empathetic, warm, talkative culinary assistant.
User message: "{query}"
{pref_str}

Respond warmly, conversationally, and helpfully like ChatGPT. If the user expresses tiredness or mood, offer comforting words and quick food ideas.
Keep response concise and engaging.
"""

    if intent == "COOKING_QUESTION":
        return f"""
You are Chef AI, a master professional chef and culinary science expert.
User Question: "{query}"
{recipe_ctx}

Provide an accurate, authoritative, step-by-step culinary response explaining temperatures, techniques, storage, or cooking science.
"""

    if intent in ["ADD_INGREDIENT", "REMOVE_INGREDIENT", "MODIFY_RECIPE", "CHANGE_SPICE_LEVEL", "MAKE_HEALTHIER", "CHANGE_DIET"]:
        return f"""
You are Chef AI, a world-class culinary research assistant.

User Modification Request: "{query}"
{recipe_ctx}
{pref_str}

Retrieved Knowledge Base Context:
{retrieved_context if retrieved_context else "Use active current recipe structure."}

MODIFICATION INSTRUCTIONS:
1. Update the active recipe title if appropriate (e.g. adding eggs to Chicken Biryani -> Chicken Biryani with Eggs).
2. Retain all core base ingredients while applying requested modifications seamlessly.
3. Update ingredients list with exact measurements.
4. Update step-by-step instructions showing when and how to cook modified items.

Output exact structured format:
Title: <Recipe Title>
Ingredients:
- <amount> <unit> <ingredient>
Instructions:
1. <Step 1>
2. <Step 2>
Chef Note: <Brief professional note>
"""

    if intent == "SUBSTITUTE_INGREDIENT":
        return f"""
You are Chef AI, specializing in USDA culinary nutrition & flavor substitutions.

User Request: "{query}"
{recipe_ctx}
{pref_str}

Explain the ideal substitute based on flavor, texture, and nutritional equivalence, then provide the updated recipe.

Output format:
Title: <Updated Recipe Title>
Ingredients:
- <amount> <unit> <ingredient>
Instructions:
1. <Step 1>
Chef Note: <Substitution advice note>
"""

    # NEW_RECIPE (Default)
    return f"""
You are Chef AI, a world-class professional culinary assistant powered by RAG technology.

User Request: "{query}"
{pref_str}

Retrieved Knowledge Base:
{retrieved_context}

Create an authentic, structured recipe based on the Knowledge Base.

Output format:
Title: <Recipe Name>
Ingredients:
- <amount> <unit> <ingredient>
Instructions:
1. <Step 1>
2. <Step 2>
Chef Note: <Flavor profile note>
"""
