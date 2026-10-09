import sys
import os
import pandas as pd
import ast
import re

sys.path.insert(0, 'Backend')
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list

def parse_raw_ing_list(raw):
    if isinstance(raw, list):
        return [str(i) for i in raw]
    if isinstance(raw, str):
        raw_s = raw.strip()
        if raw_s.startswith('[') and raw_s.endswith(']'):
            try:
                res = ast.literal_eval(raw_s)
                if isinstance(res, list):
                    return [str(i) for i in res]
            except Exception:
                pass
            return re.findall(r"['\"](.*?)['\"]", raw_s)
        return [i.strip() for i in raw_s.split(',') if i.strip()]
    return []

df = pd.read_csv('Backend/data/Recipedb_kk.csv')
asa_rows = df[df['Ingredients'].astype(str).str.contains('asafoetida|hing', case=False, na=False)]

print("Checking rows 43, 364, 573:")
for idx in [43, 364, 573]:
    if idx in df.index:
        r = df.loc[idx]
        print(f"\n--- Row {idx}: {r['Recipe Name']} ---")
        raw = r['Ingredients']
        parsed = parse_raw_ing_list(raw)
        print("Raw text:", str(raw)[:300])
        print("Parsed items:")
        for item in parsed:
            norm = normalize_ingredient(item)
            if 'asa' in item.lower() or 'hing' in item.lower() or 'asa' in norm or 'hing' in norm:
                print(f"  --> MATCH: raw='{item}' | norm='{norm}'")
            else:
                print(f"      item='{item}' | norm='{norm}'")
