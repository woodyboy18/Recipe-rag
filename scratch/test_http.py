import requests
import json

url = 'http://localhost:5000/api/query'
payload = {'query': 'give me recipes using asafoetida', 'mode': 'find'}
r = requests.post(url, json=payload)
print("Status:", r.status_code)
data = r.json()
print("Keys in response:", list(data.keys()))
print("Title:", data.get("title"))
print("Mode:", data.get("mode"))
print("Retrieved recipes count:", len(data.get("retrieved_recipes", [])))
for rec in data.get("retrieved_recipes", []):
    print("   ->", rec.get("title"))
