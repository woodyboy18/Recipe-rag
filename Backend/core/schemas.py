from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

@dataclass
class QuerySpec:
    original_query: str
    intent: str = "auto"
    mode: str = "auto"  # Valid: "auto", "find", "novel"
    ingredients_to_include: List[str] = field(default_factory=list)
    available_ingredients: List[str] = field(default_factory=list)
    ingredients_to_avoid: List[str] = field(default_factory=list)
    meal: Optional[str] = None
    diet: Optional[str] = None
    cuisine: Optional[str] = None
    max_time: Optional[int] = None
    max_calories: Optional[int] = None
    novelty_level: str = "balanced"  # Valid: "safe", "balanced", "creative"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuerySpec":
        return cls(
            original_query=data.get("original_query", ""),
            intent=data.get("intent", "auto"),
            mode=data.get("mode", "auto"),
            ingredients_to_include=data.get("ingredients_to_include", []),
            available_ingredients=data.get("available_ingredients", []),
            ingredients_to_avoid=data.get("ingredients_to_avoid", []),
            meal=data.get("meal"),
            diet=data.get("diet"),
            cuisine=data.get("cuisine"),
            max_time=data.get("max_time"),
            max_calories=data.get("max_calories"),
            novelty_level=data.get("novelty_level", "balanced"),
        )


@dataclass
class RecipeResult:
    title: str
    ingredients: List[Any]
    instructions: List[str]
    mode: str  # "retrieved" or "synthesized"
    servings: Optional[int] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    required_ingredients: List[str] = field(default_factory=list)
    avoided_ingredients: List[str] = field(default_factory=list)
    scores: Dict[str, Any] = field(default_factory=dict)
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    query: str = ""
    rewritten_query: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    retrieved_recipes: List[Dict[str, Any]] = field(default_factory=list)
    answer_raw: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "mode": self.mode,
            "servings": self.servings,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "required_ingredients": self.required_ingredients,
            "avoided_ingredients": self.avoided_ingredients,
            "scores": self.scores,
            "provenance": self.provenance,
            "query": self.query,
            "rewritten_query": self.rewritten_query,
            "constraints": self.constraints,
            "retrieved_recipes": self.retrieved_recipes,
            "answer_raw": self.answer_raw,
            # Frontend backwards compatibility fields:
            "recipe": {
                "title": self.title,
                "ingredients": self.ingredients,
                "instructions": self.instructions,
                "servings": self.servings,
                "prep_time": self.prep_time,
                "cook_time": self.cook_time,
            }
        }
