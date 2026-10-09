import requests
import json

r_health = requests.get('http://localhost:5000/api/health')
print("Health:", r_health.json())

url = 'http://localhost:5000/api/query'
payload = {'query': 'give me recipes using asafoetida', 'mode': 'find'}
r = requests.post(url, json=payload)
print("\nQuery status:", r.status_code)
data = r.json()
print("Mode:", data.get("mode"))
print("Title:", data.get("title"))
print("Retrieved recipes count:", len(data.get("retrieved_recipes", [])))
for rec in data.get("retrieved_recipes", []):
    print("   ->", rec.get("title"))
