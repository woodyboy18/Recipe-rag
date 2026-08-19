"""
Planner / Orchestrator Module (Decision Engine)
Decides what action should happen immediately after Intent Classification.
Executes internal tools conditionally to avoid unnecessary LLM and RAG calls.
"""

from state.recipe_state import RecipeState
from memory.memory_manager import ConversationMemoryManager

class ExecutionPlan:
    def __init__(
        self,
        tool_name: str,
        rag_required: bool = False,
        llm_required: bool = True,
        needs_clarification: bool = False,
        clarification_message: str = "",
        target_servings: int = None,
        target_ingredient: str = None,
        replacement_ingredient: str = None
    ):
        self.tool_name = tool_name
        self.rag_required = rag_required
        self.llm_required = llm_required
        self.needs_clarification = needs_clarification
        self.clarification_message = clarification_message
        self.target_servings = target_servings
        self.target_ingredient = target_ingredient
        self.replacement_ingredient = replacement_ingredient

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "rag_required": self.rag_required,
            "llm_required": self.llm_required,
            "needs_clarification": self.needs_clarification,
            "clarification_message": self.clarification_message
        }


def plan_execution(intent_data: dict, memory_mgr: ConversationMemoryManager) -> ExecutionPlan:
    """
    Evaluates intent, confidence score, and active recipe state to produce an ExecutionPlan.
    """
    intent = intent_data.get("intent", "UNKNOWN")
    confidence = float(intent_data.get("confidence", 1.0))
    entities = intent_data.get("entities", {})
    active_recipe = memory_mgr.active_recipe_state

    # 1. Check Confidence Threshold (< 0.65 -> Ask Clarification Question)
    if confidence < 0.65 and active_recipe:
        msg = f"Would you like me to apply this change to your current recipe '{active_recipe.title}' or create a new recipe?"
        return ExecutionPlan(
            tool_name="clarification_handler",
            rag_required=False,
            llm_required=False,
            needs_clarification=True,
            clarification_message=msg
        )

    # 2. UNDO Tool (Skips RAG & LLM)
    if intent == "UNDO":
        return ExecutionPlan(tool_name="undo_recipe", rag_required=False, llm_required=False)

    # 3. REDO Tool (Skips RAG & LLM)
    if intent == "REDO":
        return ExecutionPlan(tool_name="redo_recipe", rag_required=False, llm_required=False)

    # 4. CHANGE SERVINGS Tool (Skips RAG & LLM!)
    if intent == "CHANGE_SERVINGS":
        target = entities.get("target_servings") or 4
        return ExecutionPlan(
            tool_name="scale_recipe",
            rag_required=False,
            llm_required=False,
            target_servings=target
        )

    # 5. SUBSTITUTE INGREDIENT Tool
    if intent == "SUBSTITUTE_INGREDIENT":
        return ExecutionPlan(
            tool_name="substitute_ingredient",
            rag_required=False,
            llm_required=True,
            target_ingredient=entities.get("target_ingredient"),
            replacement_ingredient=entities.get("replacement_ingredient")
        )

    # 6. GENERAL CHAT / COOKING QUESTION Tool (Skips RAG!)
    if intent in ["GENERAL_CHAT", "COOKING_QUESTION"]:
        return ExecutionPlan(
            tool_name="cooking_question_handler",
            rag_required=False,
            llm_required=True
        )

    # 7. ADD / REMOVE / MODIFY INGREDIENT Tool (Modifies existing active recipe)
    if intent in ["ADD_INGREDIENT", "REMOVE_INGREDIENT", "MODIFY_RECIPE", "CHANGE_SPICE_LEVEL", "MAKE_HEALTHIER", "CHANGE_DIET"]:
        if active_recipe:
            return ExecutionPlan(tool_name="modify_recipe", rag_required=False, llm_required=True)
        else:
            return ExecutionPlan(tool_name="retrieve_recipe", rag_required=True, llm_required=True)

    # 8. NEW RECIPE Tool (Full RAG + LLM)
    if intent == "NEW_RECIPE":
        return ExecutionPlan(tool_name="retrieve_recipe", rag_required=True, llm_required=True)

    # Fallback
    if active_recipe:
        return ExecutionPlan(tool_name="modify_recipe", rag_required=False, llm_required=True)
    return ExecutionPlan(tool_name="retrieve_recipe", rag_required=True, llm_required=True)
