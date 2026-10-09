import sys
import os
import pandas as pd
import ast
import re

sys.path.insert(0, 'Backend')
from ingredients.normalizer import normalize_ingredient_list

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

print(f"Total rows matching asafoetida/hing: {len(asa_rows)}")

count_with_asa = 0
for idx, r in asa_rows.iterrows():
    raw_ing = r['Ingredients']
    parsed = parse_raw_ing_list(raw_ing)
    norm = normalize_ingredient_list(parsed)
    if 'asafoetida' in norm:
        count_with_asa += 1
    else:
        if count_with_asa < 3:
            print(f"\nRow {idx} title: {r['Recipe Name']}")
            print(f"  Raw items: {parsed}")
            print(f"  Norm items: {norm}")

print(f"\nNormalized count with 'asafoetida': {count_with_asa} / {len(asa_rows)}")
