"""Emit one JSON per line for each recipe (id, title, ingredients, steps),
to be consumed by the in-session estimation pass.

Run from new-app/: `python tools/emit_compact.py`
Writes to tools/recipes_compact.jsonl (UTF-8).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
recipes = json.loads((ROOT / "recipes.json").read_text(encoding="utf-8"))
out_path = ROOT / "tools" / "recipes_compact.jsonl"

with out_path.open("w", encoding="utf-8") as f:
    for r in recipes:
        out = {
            "id": r["id"],
            "title": r["title"],
            "ingredients": r.get("ingredients", []) or [],
            "steps": r.get("steps", []) or [],
        }
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
print(f"wrote {len(recipes)} recipes to {out_path}")
