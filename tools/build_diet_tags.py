"""Build assets/diet_tags.json — sidecar of régime tags for the BOOK app.

Two tag families:

1. Ingredient-based (apply to ALL 598 recipes — pure text classification):
     vegan, vegetarien, pescatarien

2. Nutrient-based (apply only to recipes that have a per-serving estimate
   in recipes_nutrition_phase2.json — currently ~198 of 598):
     faible-sucre, faible-sel, faible-gras, faible-glucides,
     riche-proteines, riche-fibres, diabetique, keto

Output schema (assets/diet_tags.json):
  {
    "schema_version": 1,
    "coverage": {
      "ingredient_based": 598,
      "nutrient_based":   N
    },
    "ingredient_tags": ["vegan", "vegetarien", "pescatarien"],
    "nutrient_tags":   ["faible-sucre", ...],
    "tags_by_recipe":  { "<recipe_id>": ["vegan", "low-sugar", ...], ... }
  }
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path("C:/Users/JonathanPrince/.claude/projects/BOOK/new-app")
RECIPES_JSON   = ROOT / "recipes.json"
# Prefer the latest phase output; fall back gracefully if phase 3 hasn't run.
NUTRITION_JSON = next(
    (ROOT / f"tools/output/recipes_nutrition_phase{p}.json"
     for p in (3, 2, 1)
     if (ROOT / f"tools/output/recipes_nutrition_phase{p}.json").exists()),
    ROOT / "tools/output/recipes_nutrition_phase2.json",
)
OUT_JSON       = ROOT / "assets/diet_tags.json"

INGREDIENT_TAGS = ["vegan", "vegetarien", "pescatarien"]
NUTRIENT_TAGS   = [
    "faible-sucre", "faible-sel", "faible-gras", "faible-glucides",
    "riche-proteines", "riche-fibres", "diabetique", "keto",
]


def norm(s: str) -> str:
    s = (s or "").lower().replace("œ", "oe")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


# Ingredient classifiers — patterns are word-boundary-anchored to avoid e.g.
# "boeuf" matching "oeuf" inside another phrase. Order: meat, fish, dairy/egg.
MEAT_PATTERNS = [re.compile(p) for p in [
    r"\bpoulet", r"\bboeuf", r"\bbifteck", r"\bsteak", r"\bveau\b",
    r"\bagneau", r"\bmouton", r"\bporc\b", r"\bjambon", r"\bbacon\b",
    r"\blard\b", r"\bsaucisse", r"\bcharcuterie", r"\bcanard", r"\bdinde",
    r"\boie\b", r"\bgibier", r"\bfoie",
    r"\bbouillon de (?:poulet|boeuf|viande)",
    r"\bcrouton de boeuf",
    r"\bhamburger\b",
    # Note: NOT \bhache\b — too noisy ("oignons hachés" is not meat).
]]
FISH_PATTERNS = [re.compile(p) for p in [
    r"\bpoisson", r"\bsaumon", r"\bmorue", r"\bthon\b", r"\bsardine",
    r"\btruite", r"\bfletan", r"\bsole\b", r"\btilapia",
    r"\bcrevette", r"\bhomard", r"\bcrabe", r"\bpetoncle", r"\bhuitre",
    r"\bcalmar", r"\bmoule\b", r"\bmoules", r"\bfruits? de mer",
    r"\banchois", r"\bmahi", r"\bcarrelet",
]]
DAIRY_EGG_PATTERNS = [re.compile(p) for p in [
    r"\bbeurre\b", r"\blait\b", r"\bcreme\b", r"\bfromage", r"\boeuf",
    r"\byogourt", r"\byaourt", r"\bmiel\b", r"\bgelatine",
    r"\bphiladelphia", r"\bricotta", r"\bmozzarella", r"\bparmesan",
    r"\bcheddar", r"\bbrie", r"\bfeta", r"\bcottage", r"\bgruyere",
]]


def has_any(text: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def classify_ingredient_diets(recipe: dict) -> list[str]:
    """Return ingredient-based diet tags this recipe satisfies."""
    text = norm(" ".join(recipe.get("ingredients") or []))
    has_meat  = has_any(text, MEAT_PATTERNS)
    has_fish  = has_any(text, FISH_PATTERNS)
    has_dairy = has_any(text, DAIRY_EGG_PATTERNS)
    out: list[str] = []
    if not has_meat and not has_fish and not has_dairy:
        out.append("vegan")
    if not has_meat and not has_fish:
        out.append("vegetarien")
    if not has_meat:
        out.append("pescatarien")
    return out


def classify_nutrient_diets(per_serving: dict | None) -> list[str]:
    """Return nutrient-based diet tags this recipe satisfies (per serving)."""
    if not per_serving:
        return []
    out: list[str] = []
    p = per_serving
    energy = p.get("energy_kcal", 0) or 0
    fat    = p.get("fat_g", 0) or 0
    carbs  = p.get("carbohydrate_g", 0) or 0
    fiber  = p.get("fiber_g", 0) or 0
    sugars = p.get("sugars_g", 0) or 0
    sodium = p.get("sodium_mg", 0) or 0
    protein = p.get("protein_g", 0) or 0

    # Per-serving thresholds, aligned with FDA/Health Canada-style claims
    if sugars  <= 5:    out.append("faible-sucre")
    if sodium  <= 140:  out.append("faible-sel")
    if fat     <= 10:   out.append("faible-gras")
    if carbs   <= 20:   out.append("faible-glucides")
    if protein >= 20:   out.append("riche-proteines")
    if fiber   >= 5:    out.append("riche-fibres")
    if sugars  <= 10 and carbs <= 45:  out.append("diabetique")

    # Keto: <=10g net carbs AND >=65% kcal from fat
    net_carbs = max(carbs - fiber, 0)
    if energy > 0:
        fat_pct = (9 * fat) / energy
        if net_carbs <= 10 and fat_pct >= 0.65:
            out.append("keto")
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print(f"Loading {RECIPES_JSON}")
    with open(RECIPES_JSON, encoding="utf-8") as f:
        recipes = json.load(f)
    print(f"  {len(recipes)} recipes")

    nutrition_by_id: dict = {}
    if NUTRITION_JSON.exists():
        with open(NUTRITION_JSON, encoding="utf-8") as f:
            nut = json.load(f)
        for r in nut["recipes"]:
            nutrition_by_id[r["id"]] = r
        print(f"  {len(nutrition_by_id)} recipes with nutrition estimates")
    else:
        print("  WARN: nutrition file not found — nutrient tags will be empty")

    tags_by_recipe: dict[str, list[str]] = {}
    nut_eligible = 0
    counts: dict[str, int] = {t: 0 for t in INGREDIENT_TAGS + NUTRIENT_TAGS}
    for r in recipes:
        rid = str(r["id"])
        ing_tags = classify_ingredient_diets(r)
        n = nutrition_by_id.get(r["id"])
        per_serving = (n or {}).get("per_serving")
        nut_tags = classify_nutrient_diets(per_serving)
        if per_serving:
            nut_eligible += 1
        all_tags = ing_tags + nut_tags
        if all_tags:
            tags_by_recipe[rid] = all_tags
        for t in all_tags:
            counts[t] = counts.get(t, 0) + 1

    payload = {
        "schema_version": 1,
        "coverage": {
            "total_recipes":    len(recipes),
            "ingredient_based": len(recipes),
            "nutrient_based":   nut_eligible,
        },
        "ingredient_tags": INGREDIENT_TAGS,
        "nutrient_tags":   NUTRIENT_TAGS,
        "tags_by_recipe":  tags_by_recipe,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {OUT_JSON}")

    print("\n=== Tag counts ===")
    for t in INGREDIENT_TAGS:
        print(f"  {t:20s} {counts.get(t,0):>4} recipes  (pool: {len(recipes)})")
    print(f"  --- nutrient-based (pool: {nut_eligible}) ---")
    for t in NUTRIENT_TAGS:
        print(f"  {t:20s} {counts.get(t,0):>4} recipes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
