"""Build assets/recipes_nutrition.json — slim production sidecar.

Reads the latest phase output from tools/output/recipes_nutrition_phase{3,2,1}.json
and writes a lean per-recipe nutrient map for the BOOK app to consume.

The phase outputs include per-ingredient debug data (food_id, match_source,
conv_method, etc.) that is useful for review CSVs but bloats the file the
browser loads on every page. This script keeps only what the recipe-detail
panel needs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/JonathanPrince/.claude/projects/BOOK/new-app")
OUT_JSON = ROOT / "assets/recipes_nutrition.json"

# Pick the latest phase output that exists.
SOURCE = next(
    (ROOT / f"tools/output/recipes_nutrition_phase{p}.json"
     for p in (3, 2, 1)
     if (ROOT / f"tools/output/recipes_nutrition_phase{p}.json").exists()),
    None,
)

# Nutrients shown in the recipe-detail panel, in the order they appear.
# `sub` flags subordinate rows ("dont X") for indented styling.
DISPLAYED_NUTRIENTS = [
    {"id": "energy_kcal",     "label": "Énergie",       "unit": "kcal", "decimals": 0},
    {"id": "protein_g",       "label": "Protéines",     "unit": "g",    "decimals": 1},
    {"id": "fat_g",           "label": "Lipides",       "unit": "g",    "decimals": 1},
    {"id": "saturated_fat_g", "label": "dont saturés",  "unit": "g",    "decimals": 1, "sub": True},
    {"id": "carbohydrate_g",  "label": "Glucides",      "unit": "g",    "decimals": 1},
    {"id": "fiber_g",         "label": "dont fibres",   "unit": "g",    "decimals": 1, "sub": True},
    {"id": "sugars_g",        "label": "dont sucres",   "unit": "g",    "decimals": 1, "sub": True},
    {"id": "sodium_mg",       "label": "Sodium",        "unit": "mg",   "decimals": 0},
    {"id": "calcium_mg",      "label": "Calcium",       "unit": "mg",   "decimals": 0},
    {"id": "iron_mg",         "label": "Fer",           "unit": "mg",   "decimals": 1},
    {"id": "vitamin_c_mg",    "label": "Vitamine C",    "unit": "mg",   "decimals": 0},
    {"id": "potassium_mg",    "label": "Potassium",     "unit": "mg",   "decimals": 0},
]
KEPT = {n["id"] for n in DISPLAYED_NUTRIENTS}


def slim(per_dict: dict | None) -> dict | None:
    if not per_dict:
        return None
    return {k: round(v, 2) for k, v in per_dict.items() if k in KEPT and v is not None}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if SOURCE is None or not SOURCE.exists():
        print(f"ERROR: no phase output found under {ROOT / 'tools/output'}", file=sys.stderr)
        return 1
    print(f"Loading {SOURCE}")
    with open(SOURCE, encoding="utf-8") as f:
        src = json.load(f)

    by_recipe: dict[str, dict] = {}
    for r in src["recipes"]:
        per_s = slim(r.get("per_serving"))
        per_100g = slim(r.get("per_100g"))
        # If neither view has data, skip — there's nothing useful to show.
        if not per_s and not per_100g:
            continue
        by_recipe[str(r["id"])] = {
            "servings":         r.get("servings"),
            "servings_imputed": r.get("servings_imputed", False),
            "total_grams":      round(r.get("total_grams") or 0, 1),
            "low_conf_ratio":   round(r.get("low_conf_ratio") or 0, 3),
            "match_count":      r.get("matched_count", 0),
            "ingredient_count": r.get("ingredient_count", 0),
            "skipped_unquantified": r.get("skipped_unquantified", 0),
            "per_serving":      per_s,
            "per_100g":         per_100g,
        }

    payload = {
        "schema_version": 1,
        "generated_from": SOURCE.name,
        "displayed_nutrients": DISPLAYED_NUTRIENTS,
        "by_recipe": by_recipe,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = OUT_JSON.stat().st_size / 1024
    print(f"Wrote {OUT_JSON} ({len(by_recipe)} recipes, {size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
