import sys
import os

sys.path.insert(0, 'Backend')
from api_server import app, recipe_engine

client = app.test_client()

res_health = client.get('/api/health')
print("Health status code:", res_health.status_code)
print("Health json:", res_health.get_json())
print("recipe_engine._df len:", len(recipe_engine._df) if recipe_engine._df is not None else "None")

res_query = client.post('/api/query', json={'query': 'give me recipes using asafoetida', 'mode': 'find'})
print("\nQuery status code:", res_query.status_code)
q_json = res_query.get_json()
print("Query mode:", q_json.get("mode"))
print("Query title:", q_json.get("title"))
print("Query retrieved count:", len(q_json.get("retrieved_recipes", [])))
for r in q_json.get("retrieved_recipes", []):
    print("   ->", r.get("title"))
