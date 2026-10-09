import requests
import json

def test_query(q, mode='auto'):
    url = 'http://localhost:5000/api/query'
    payload = {'query': q, 'mode': mode, 'novelty': 'balanced'}
    try:
        r = requests.post(url, json=payload, timeout=20)
        print(f"=== QUERY: '{q}' (mode={mode}) ===")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print("Mode:", data.get("mode"))
            print("Title:", data.get("title"))
            
            ings = data.get("ingredients", [])
            print(f"Ingredients count: {len(ings)}")
            for ing in ings[:6]:
                print(f"   - {ing}")

            insts = data.get("instructions", [])
            print(f"Instructions count: {len(insts)}")
            for st in insts[:3]:
                if isinstance(st, dict):
                    print(f"   Step {st.get('step')}: {st.get('text')}")
                else:
                    print(f"   Step: {st}")

            ret_recs = data.get("retrieved_recipes", [])
            print(f"Retrieved recipes count: {len(ret_recs)}")
            for rr in ret_recs[:3]:
                print(f"   [Retrieved] {rr.get('title')} (RRF={rr.get('rrf_score')})")
        else:
            print("Error output:", r.text[:200])
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test_query("give me recipes using asafoetida", "find")
    print("-" * 60)
    test_query("asafoetida", "find")
    print("-" * 60)
    test_query("create a new recipe using asafoetida", "novel")
