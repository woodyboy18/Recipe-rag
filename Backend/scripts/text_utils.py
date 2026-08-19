"""Text helpers shared by index building, retrieval, and prompt construction."""
import ast
import re

# Words that carry no food-matching signal. Conservative — never drops
# ingredient/method words (chicken, fry, rice, ...).
_STOPWORDS = frozenset(
    """a an and any are as at be by for from has have how in into is it its make
    makes making my of on or per so that the to with without would you your
    please recipe recipes using use used""".split()
)

_WS = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return _WS.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    """Word-boundary tokens with stopwords and pure quantities removed."""
    return [
        t for t in clean_text(text).split()
        if t not in _STOPWORDS and not t.isdigit()
    ]


def parse_recipe_list(value) -> list[str]:
    """Parse a Python-list-as-string cell (e.g. "['a', 'b']") into a list.

    Falls back to a safe comma split for malformed cells.
    """
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if not isinstance(value, str) or not value.strip():
        return []
    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except (ValueError, SyntaxError):
            pass
    return [part.strip() for part in text.split(",") if part.strip()]


def build_search_text(title: str, ingredients: list[str], max_ingredients: int = 10) -> str:
    """Short, searchable text used for embedding. Keeps recipe identity and the
    ingredients that intent queries actually match; stays under MiniLM's
    256-token window instead of being diluted by long instruction text."""
    ing = ", ".join(ingredients[:max_ingredients])
    return f"Recipe Name: {title}\nIngredients: {ing}"


def format_recipe_block(rank: int, title: str, ingredients: list[str],
                        instructions: list[str], max_chars: int = 900) -> str:
    """Render one retrieved recipe for the LLM prompt context."""
    ing = ", ".join(ingredients[:12])
    steps = " ".join(instructions[:3]) if instructions else "No instructions."
    block = f"[{rank}] Title: {title}\n Ingredients: {ing}\n Steps: {steps}"
    return block[:max_chars]
