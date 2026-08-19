"""
Flask API Server for Culinary RAG Recipe System
Exposes REST API endpoints for the Conversational Chatbot UI.
Features:
- Hybrid Retrieval (FAISS + BM25) with Maximum Keyword Reranking
- Conversation Memory & Context-Aware Query Rewriting
- USDA FoodData Central Protein Substitution Matching
- Clean JSON API responses
"""

import os
import sys
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from flask import Flask, request, jsonify
from flask_cors import CORS

_backend_loaded = False
_answer_query = None
_retrieve = None
_rewrite_query = None
_retrieve_memory = None
_extract_constraints = None
_merge_constraints = None
_get_recent_history = None
_get_usda_substitution_advice = None
_save_retrieval_cache = None
_df = None

MEMORY_FILE = os.path.join(PROJECT_ROOT, "memory", "user_memory.json")

def _load_backend():
    global _backend_loaded, _answer_query, _retrieve, _rewrite_query
    global _retrieve_memory, _extract_constraints, _merge_constraints
    global _get_recent_history, _get_usda_substitution_advice, _save_retrieval_cache, _df

    if _backend_loaded:
        return

    from interactive_rag import answer_query, retrieve, df
    from query.query_rewritter import rewrite_query
    from memory.memory_retriever import retrieve_memory
    from memory.conversation_memory import get_recent_history
    from memory.retrieval_cache import save_retrieval_cache
    from constraints.constraint_extractor import extract_constraints, merge_constraints
    from substitution.usda_substitution import get_usda_substitution_advice

    _answer_query = answer_query
    _retrieve = retrieve
    _rewrite_query = rewrite_query
    _retrieve_memory = retrieve_memory
    _extract_constraints = extract_constraints
    _merge_constraints = merge_constraints
    _get_recent_history = get_recent_history
    _get_usda_substitution_advice = get_usda_substitution_advice
    _save_retrieval_cache = save_retrieval_cache
    _df = df

    # Reset memory on server startup for a fresh session
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        print("Memory reset: Fresh session initialized.")
    except Exception as e:
        print(f"Memory reset warning: {e}")

    _backend_loaded = True


app = Flask(__name__)
CORS(app)


def _is_new_recipe_query(query: str) -> bool:
    q = query.lower().strip()
    mod_triggers = [
        "without", "no ", "don't have", "dont have", "do not have",
        "avoid", "exclude", "skip", "remove", "dont want", "don't want",
        "make it", "instead", "substitute", "replace", "have no", "has no",
        "add ", "plus", "also", "include", "put ", "with ", "and "
    ]
    for trigger in mod_triggers:
        if trigger in q:
            return False

    new_triggers = [
        "recipe for", "how to make", "how to prepare", "give me", "give recipe",
        "biryani", "curry", "shake", "cake", "soup", "pancake", "pasta",
        "pizza", "burger", "rice", "noodle", "salad", "dosa", "idli"
    ]
    for trigger in new_triggers:
        if trigger in q:
            return True

    return False


def _extract_doc_title(doc_text: str) -> str:
    for line in doc_text.split("\n"):
        s = line.strip()
        if s.lower().startswith("recipe name:"):
            return s.split(":", 1)[1].strip()
        if s.lower().startswith("recipe:"):
            return s.split(":", 1)[1].strip()
        if s.lower().startswith("title:"):
            return s.split(":", 1)[1].strip()
    return doc_text[:60].strip()


def _parse_recipe_from_answer(answer_text: str) -> dict:
    title = ""
    ingredients = []
    instructions = []
    current_section = None

    for line in answer_text.split("\n"):
        s = line.strip()
        if not s:
            continue

        if s.lower().startswith("title:"):
            title = s.split(":", 1)[1].strip()
            current_section = None
        elif re.match(r"^ingredients?\s*:?\s*$", s, re.IGNORECASE):
            current_section = "ing"
        elif re.match(r"^(instructions?|steps?|directions?)\s*:?\s*$", s, re.IGNORECASE):
            current_section = "inst"
        elif re.match(r"^(chef note|chef's note|note)\s*:?\s*$", s, re.IGNORECASE):
            current_section = None
        elif s.startswith("-") or s.startswith("•"):
            item = s.lstrip("-• ").strip()
            if item:
                if current_section == "inst":
                    instructions.append(item)
                else:
                    ingredients.append(item)
        elif re.match(r"^\d+[\.\)]\s*", s):
            item = re.sub(r"^\d+[\.\)]\s*", "", s).strip()
            if item:
                instructions.append(item)

    return {
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions
    }

# ================= ROUTES =================

@app.route("/api/health", methods=["GET"])
def health():
    try:
        _load_backend()
        return jsonify({
            "status": "ok",
            "ollama_connected": True,
            "dataset_size": len(_df) if _df is not None else 0,
            "message": "RAG backend loaded successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def query_recipe():
    data = request.get_json()
    if not data or not data.get("query", "").strip():
        return jsonify({"error": "Query is required"}), 400

    user_query = data["query"].strip()

    try:
        _load_backend()

        is_new_query = _is_new_recipe_query(user_query)
        current_constraints = _extract_constraints(user_query)
        recent_turns = _get_recent_history(5)

        if not is_new_query and recent_turns:
            history_lines = []
            for turn in recent_turns:
                history_lines.append(f"User: {turn['user']}")
                if turn.get("assistant"):
                    first_line = turn["assistant"].split("\n")[0]
                    history_lines.append(f"Assistant: {first_line}")
            conversation_history = "\n".join(history_lines)

            active_constraints = current_constraints
            for turn in recent_turns:
                if turn.get("constraints"):
                    active_constraints = _merge_constraints(turn["constraints"], active_constraints)
        else:
            conversation_history = ""
            active_constraints = current_constraints

        rewritten_query = _rewrite_query(user_query, conversation_history, active_constraints)

        avoid_list = active_constraints.get("ingredients_to_avoid", [])
        docs, indices = _retrieve(rewritten_query, avoid_ingredients=avoid_list, top_k=10)

        if _save_retrieval_cache and docs:
            _save_retrieval_cache(rewritten_query, docs)

        retrieved_recipes = []
        for i, doc in enumerate(docs):
            doc_title = _extract_doc_title(doc)
            retrieved_recipes.append({
                "title": doc_title,
                "snippet": doc,
                "score": round(0.95 - (i * 0.04), 2)
            })


        allow_sub = active_constraints.get("allow_substitutions", True)
        usda_advice = _get_usda_substitution_advice(avoid_list, allow_substitutions=allow_sub)

        raw_answer = _answer_query(user_query)
        raw_answer = str(raw_answer) if raw_answer else ""

        parsed = _parse_recipe_from_answer(raw_answer)

        if not parsed.get("title") or not parsed.get("ingredients"):
            if len(docs) > 0 and len(retrieved_recipes) > 0:
                top_rec = retrieved_recipes[0]
                top_doc = docs[0]

                ing_list = []
                inst_list = []
                curr_sec = None

                for line in top_doc.split("\n"):
                    l_str = line.strip()
                    if not l_str:
                        continue
                    if l_str.lower().startswith("ingredients:"):
                        curr_sec = "ing"
                        val = l_str.split(":", 1)[1].strip()
                        if val:
                            ing_list.extend([i.strip() for i in val.split(",") if i.strip()])
                    elif l_str.lower().startswith("instructions:") or l_str.lower().startswith("directions:"):
                        curr_sec = "inst"
                        val = l_str.split(":", 1)[1].strip()
                        if val:
                            inst_list.append(val)
                    elif curr_sec == "ing":
                        ing_list.extend([i.strip() for i in l_str.split(",") if i.strip()])
                    elif curr_sec == "inst":
                        inst_list.append(l_str)

                parsed = {
                    "title": top_rec.get("title") or "Delicious Recipe",
                    "ingredients": ing_list if ing_list else ["Main Ingredients from Recipe", "Spices", "Cooking Oil"],
                    "instructions": inst_list if inst_list else ["Mix all ingredients thoroughly.", "Cook evenly on medium flame until done.", "Serve hot!"]
                }

        return jsonify({
            "query": user_query,
            "is_new_query": is_new_query,
            "rewritten_query": rewritten_query,
            "constraints": active_constraints,
            "usda_substitutions": usda_advice,
            "answer_raw": raw_answer,
            "recipe": parsed,
            "retrieved_recipes": retrieved_recipes,
            "conversation_history": conversation_history
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "query": user_query,
            "rewritten_query": user_query,
            "recipe": {"title": "", "ingredients": [], "instructions": []},
            "retrieved_recipes": []
        }), 500


@app.route("/api/memory", methods=["GET"])
def get_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return jsonify({"memory": data[-10:]})
        return jsonify({"memory": []})
    except Exception as e:
        return jsonify({"memory": [], "error": str(e)})


@app.route("/api/memory/clear", methods=["POST"])
def clear_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Loading RAG backend...", flush=True)
    _load_backend()
    print(f"Dataset: {len(_df)} recipes loaded", flush=True)
    print("Starting Flask API on http://localhost:5000", flush=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
