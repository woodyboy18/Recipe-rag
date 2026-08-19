"""
Structured Recipe State Module
Defines the canonical RecipeState object and programmatic mutation methods.
Zero hardcoded dish names or ingredient rules.
"""

import uuid
import copy
import re

class RecipeIngredient:
    def __init__(self, name: str, amount: float = 1.0, unit: str = "", notes: str = ""):
        self.name = name.strip()
        self.amount = float(amount) if amount else 1.0
        self.unit = unit.strip()
        self.notes = notes.strip()

    def to_dict(self):
        return {
            "name": self.name,
            "amount": round(self.amount, 2),
            "unit": self.unit,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            name=d.get("name", ""),
            amount=d.get("amount", 1.0),
            unit=d.get("unit", ""),
            notes=d.get("notes", "")
        )


class RecipeState:
    def __init__(
        self,
        title: str = "Untitled Recipe",
        description: str = "",
        ingredients: list = None,
        instructions: list = None,
        nutrition: dict = None,
        cook_time_mins: int = 30,
        prep_time_mins: int = 15,
        servings: int = 2,
        difficulty: str = "Medium",
        image_url: str = "",
        retrieved_documents: list = None,
        similarity_scores: list = None,
        version: int = 1,
        recipe_id: str = None
    ):
        self.id = recipe_id or f"rec_{uuid.uuid4().hex[:8]}"
        self.title = title.strip()
        self.description = description.strip()
        
        # Process ingredients into RecipeIngredient objects
        self.ingredients = []
        if ingredients:
            for ing in ingredients:
                if isinstance(ing, RecipeIngredient):
                    self.ingredients.append(ing)
                elif isinstance(ing, dict):
                    self.ingredients.append(RecipeIngredient.from_dict(ing))
                elif isinstance(ing, str):
                    self.ingredients.append(self._parse_ingredient_string(ing))

        self.instructions = [str(inst).strip() for inst in (instructions or []) if str(inst).strip()]
        self.nutrition = nutrition or {"calories": 500, "protein_g": 30, "carbs_g": 40, "fat_g": 18}
        self.cook_time_mins = int(cook_time_mins) if cook_time_mins else 30
        self.prep_time_mins = int(prep_time_mins) if prep_time_mins else 15
        self.servings = int(servings) if servings else 2
        self.difficulty = difficulty
        self.image_url = image_url
        self.retrieved_documents = retrieved_documents or []
        self.similarity_scores = similarity_scores or []
        self.version = int(version)

    def _parse_ingredient_string(self, text: str) -> RecipeIngredient:
        text_clean = text.lstrip("-• ").strip()
        # Parse optional amount and unit
        match = re.match(r"^([\d\.\/\s]+)\s*([a-zA-Z]+)?\s+(.*)$", text_clean)
        if match:
            raw_amt, unit, name = match.groups()
            try:
                if "/" in raw_amt:
                    num, den = raw_amt.split("/")
                    amt = float(num.strip()) / float(den.strip())
                else:
                    amt = float(raw_amt.strip())
            except Exception:
                amt = 1.0
            return RecipeIngredient(name=name.strip(), amount=amt, unit=unit or "")
        return RecipeIngredient(name=text_clean, amount=1.0, unit="")

    def scale_servings(self, target_servings: int) -> "RecipeState":
        if target_servings <= 0 or self.servings <= 0:
            return self

        ratio = float(target_servings) / float(self.servings)
        new_state = copy.deepcopy(self)
        new_state.servings = int(target_servings)

        for ing in new_state.ingredients:
            ing.amount = round(ing.amount * ratio, 2)

        if "calories" in new_state.nutrition:
            new_state.nutrition["calories"] = int(new_state.nutrition["calories"] * ratio)

        new_state.version += 1
        return new_state

    def add_ingredient(self, name: str, amount: float = 1.0, unit: str = "") -> "RecipeState":
        new_state = copy.deepcopy(self)
        # Check if already present
        for ing in new_state.ingredients:
            if ing.name.lower() == name.lower():
                ing.amount += amount
                new_state.version += 1
                return new_state

        new_state.ingredients.append(RecipeIngredient(name=name, amount=amount, unit=unit))
        # Add basic instruction step for new ingredient
        new_state.instructions.append(f"Incorporate {name} evenly into the dish during cooking.")
        new_state.version += 1
        return new_state

    def remove_ingredient(self, name: str) -> "RecipeState":
        new_state = copy.deepcopy(self)
        term = name.lower().strip()
        new_state.ingredients = [ing for ing in new_state.ingredients if term not in ing.name.lower()]

        # Filter out instructions specifically mentioning removed ingredient
        new_instructions = []
        for inst in new_state.instructions:
            pattern = r"\b" + re.escape(term) + r"(?:s|es)?\b"
            if not re.search(pattern, inst.lower()):
                new_instructions.append(inst)

        new_state.instructions = new_instructions if new_instructions else new_state.instructions
        new_state.version += 1
        return new_state

    def substitute_ingredient(self, target_name: str, replacement_name: str) -> "RecipeState":
        new_state = copy.deepcopy(self)
        t_term = target_name.lower().strip()
        r_term = replacement_name.strip()

        replaced = False
        for ing in new_state.ingredients:
            if t_term in ing.name.lower():
                ing.name = r_term
                replaced = True

        if not replaced:
            new_state.ingredients.append(RecipeIngredient(name=r_term, amount=1.0, unit=""))

        # Update instructions
        new_insts = []
        for inst in new_state.instructions:
            updated_inst = re.sub(r"\b" + re.escape(t_term) + r"(?:s|es)?\b", r_term, inst, flags=re.IGNORECASE)
            new_insts.append(updated_inst)
        new_state.instructions = new_insts

        new_state.version += 1
        return new_state

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "instructions": self.instructions,
            "nutrition": self.nutrition,
            "cook_time_mins": self.cook_time_mins,
            "prep_time_mins": self.prep_time_mins,
            "servings": self.servings,
            "difficulty": self.difficulty,
            "image_url": self.image_url,
            "retrieved_documents": self.retrieved_documents,
            "similarity_scores": self.similarity_scores,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            recipe_id=d.get("id"),
            title=d.get("title", "Untitled Recipe"),
            description=d.get("description", ""),
            ingredients=d.get("ingredients", []),
            instructions=d.get("instructions", []),
            nutrition=d.get("nutrition"),
            cook_time_mins=d.get("cook_time_mins", 30),
            prep_time_mins=d.get("prep_time_mins", 15),
            servings=d.get("servings", 2),
            difficulty=d.get("difficulty", "Medium"),
            image_url=d.get("image_url", ""),
            retrieved_documents=d.get("retrieved_documents", []),
            similarity_scores=d.get("similarity_scores", []),
            version=d.get("version", 1)
        )
