"""
Flask API Server for Culinary RAG Recipe System
Exposes REST API endpoints for the Conversational Chatbot UI.
Features Grounded Novel Recipe Synthesis Engine with Mode & Novelty Level Routing.
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import core.recipe_engine as recipe_engine
from memory.conversation_memory import save_turn, get_recent_history, clear_history

MEMORY_FILE = os.path.join(PROJECT_ROOT, "memory", "user_memory.json")

app = Flask(__name__)
CORS(app)

_server_initialized = False

def _ensure_backend():
    if recipe_engine._df is None or len(recipe_engine._df) == 0:
        recipe_engine.initialize_engine()


@app.route("/api/health", methods=["GET"])
def health():
    try:
        _ensure_backend()
        df = recipe_engine._df
        dataset_len = len(df) if df is not None else 0
        ing_idx = recipe_engine._ingredient_index
        asa_in_idx = ('asafoetida' in ing_idx.index) if ing_idx else False
        asa_count = len(ing_idx.index.get('asafoetida', [])) if asa_in_idx else 0
        return jsonify({
            "status": "ok",
            "model": "mistral:latest",
            "recipe_count": dataset_len,
            "asafoetida_in_index": asa_in_idx,
            "asafoetida_recipe_count": asa_count,
            "message": "Grounded Novel Recipe RAG Server Running"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def query_recipe():
    data = request.get_json() or {}
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"error": "Query parameter is required"}), 400

    requested_mode = data.get("mode", "auto")
    novelty_level = data.get("novelty_level", "balanced")

    try:
        _ensure_backend()

        # Process via central recipe engine
        result_dict = recipe_engine.answer_query(
            query=user_query,
            requested_mode=requested_mode,
            novelty_level=novelty_level
        )

        # Save conversation history turn
        try:
            assistant_summary = f"{result_dict.get('title', '')} ({result_dict.get('mode', 'retrieved')})"
            save_turn(user_query, assistant_summary, str(result_dict.get("constraints", {})))
        except Exception:
            pass

        from core.schemas import _sanitize_json
        return jsonify(_sanitize_json(result_dict))

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"ERROR IN QUERY_RECIPE:\n{err_msg}", flush=True)
        return jsonify({
            "error": "Failed to process recipe query",
            "details": str(e),
            "traceback": err_msg,
            "query": user_query,
            "mode": "retrieved",
            "recipe": {"title": "Error processing query", "ingredients": [], "instructions": [str(e)]},
            "retrieved_recipes": [],
            "scores": {},
            "provenance": []
        })


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
def clear_memory_route():
    try:
        clear_history()
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    _ensure_backend()
    print("Starting Flask API Server on http://localhost:5000...", flush=True)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
