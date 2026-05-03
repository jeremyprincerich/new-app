"""Phase 3 meta extension: fills meta for IDs >= 317 (corrected sideways
plus all recipes added by the BOOK1 second-pass pipeline).

Strategy:
- Hard overrides for IDs where I have judgment-based estimates.
- Default soup-shape (prep 15, cook 30, servings 6, facile) for IDs 335-700
  not covered by the hard overrides; protein tags auto-detected from text.
- "Suite de la recette précédente" entries inherit meta from the prior id.
- "Page photographiée à l'horizontale" stubs get null meta.

Run from new-app/: `python tools/meta_phase3.py`

Idempotent — re-running is safe and overwrites with the same values.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes.json"

PROTEIN_KEYWORDS = {
    "poulet": ["poulet", "poitrines de poulet", "carcasse"],
    "boeuf": ["bœuf", "boeuf", "bourguignon", "haché", "consommé de bœuf", "rôti", "steak"],
    "porc": ["porc", "saucisse", "saucisson", "lardon", "kielbasa"],
    "veau": ["veau", "halloumi"],
    "agneau": ["agneau"],
    "poisson": ["poisson", "saumon", "morue", "merlan", "truite"],
    "fruits-de-mer": [
        "crevette", "palourde", "homard", "calmar", "fruits de mer",
        "moule", "pétoncle", "crabe", "wonton",
    ],
    "jambon": ["jambon", "prosciutto", "bacon"],
}


def detect_proteins(text: str) -> list[str]:
    text_l = text.lower()
    found = []
    for tag, words in PROTEIN_KEYWORDS.items():
        if any(w in text_l for w in words):
            found.append(tag)
    return found


def make_meta(prep, cook, serv, yc, yu, diff, tags):
    return {
        "prepMinutes": prep,
        "cookMinutes": cook,
        "servings": serv,
        "yieldCount": yc,
        "yieldUnit": yu,
        "difficulty": diff,
        "tags": list(tags) if tags else [],
    }


# Hard meta overrides. Tuple shape:
# (prep, cook, servings, yieldCount, yieldUnit, difficulty, [tags])
PHASE3_META = {
    # Sideways pages corrected via merge_book1_v2.py — IDs 317-334.
    317: (15, 30, 4, None, None, "facile", ["vegetarien"]),
    318: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    319: (20, 45, 6, None, None, "moyen", ["vegetarien"]),
    320: (15, 60, 6, None, None, "facile", ["jambon"]),
    321: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    322: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    323: (20, 60, 8, None, None, "facile", ["boeuf", "long-mijotage"]),
    324: (20, 40, 6, None, None, "facile", ["vegetarien"]),
    325: (15, 20, 6, None, None, "facile", ["vegetarien", "rapide"]),
    326: (20, 40, 6, None, None, "moyen", ["poulet"]),
    327: (15, 45, 6, None, None, "facile", ["vegetarien"]),
    328: (20, 25, 6, None, None, "facile", ["vegetarien"]),
    329: (20, 25, 6, None, None, "moyen", ["vegetarien"]),
    330: (15, 35, 6, None, None, "facile", ["vegetarien"]),
    331: (15, 60, 6, None, None, "facile", ["vegetarien"]),
    332: (15, 25, 6, None, None, "facile", ["vegetarien"]),
    333: (20, 25, 6, None, None, "moyen", ["fruits-de-mer"]),
    334: (15, 25, 6, None, None, "facile", ["vegetarien"]),

    # Selected hard estimates for the second-pass IDs (335-512).
    335: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    336: (5, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    339: (20, 30, 6, None, None, "moyen", ["fruits-de-mer"]),
    340: (20, 30, 6, None, None, "moyen", ["poisson"]),
    345: (20, 25, 4, None, None, "moyen", ["poisson", "fruits-de-mer"]),
    347: (20, 60, 8, None, None, "facile", ["porc"]),
    349: (25, 50, 8, None, None, "moyen", ["boeuf"]),
    353: (20, 90, 8, None, None, "facile", ["vegetarien", "long-mijotage"]),
    359: (20, 105, 8, None, None, "moyen", ["boeuf", "long-mijotage"]),
    361: (20, 60, 8, None, None, "facile", ["poulet"]),
    366: (15, 150, 8, None, None, "facile", ["porc", "long-mijotage"]),
    369: (25, 30, 6, None, None, "moyen", ["vegetarien", "four"]),
    378: (20, 90, 8, None, None, "moyen", ["boeuf", "long-mijotage"]),
    386: (25, 30, 6, None, None, "moyen", ["fruits-de-mer", "poisson"]),
    388: (30, 30, 6, None, None, "moyen", ["fruits-de-mer", "poisson"]),
    412: (20, 90, 8, None, None, "moyen", ["boeuf", "long-mijotage"]),
    420: (25, 60, 6, None, None, "moyen", ["boeuf"]),
    433: (20, 360, 8, None, None, "facile", ["boeuf", "mijoteuse"]),
    434: (20, 90, 8, None, None, "moyen", ["boeuf", "long-mijotage"]),
    461: (20, 90, 6, None, None, "facile", ["poulet", "long-mijotage"]),
    463: (15, 120, 8, None, None, "facile", ["poulet", "long-mijotage"]),
    466: (10, 120, None, 8, "tasses", "facile", ["poulet", "long-mijotage", "congelation"]),
    470: (25, 90, 8, None, None, "moyen", ["boeuf", "long-mijotage"]),
    476: (10, 120, None, 5, "tasses", "facile", ["boeuf", "long-mijotage", "congelation"]),
    477: (10, 120, None, 5, "tasses", "facile", ["poulet", "long-mijotage", "congelation"]),
    509: (35, 90, 6, None, None, "difficile", ["veau", "long-mijotage"]),
    510: (20, 105, 8, None, None, "facile", ["jambon", "long-mijotage"]),
    511: (20, 30, 4, None, None, "moyen", ["poulet"]),
    512: (25, 35, 4, None, None, "moyen", ["vegetarien"]),
}


def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in recipes}

    # Apply hard overrides.
    for rid, t in PHASE3_META.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        rec["meta"] = make_meta(*t)

    # Default for any 335-700 entry not in PHASE3_META.
    # Inherit from previous id when title starts with "Suite de la recette".
    # Reserves headroom for ongoing additions.
    for rid in range(335, 700):
        rec = by_id.get(rid)
        if rec is None:
            continue
        if rid in PHASE3_META:
            continue
        title = (rec.get("title") or "").lower()
        if "page photographi" in title or "transcription incompl" in title:
            rec["meta"] = make_meta(None, None, None, None, None, None, [])
            continue
        if title.startswith("suite de la recette") or title.startswith("variante"):
            prev = by_id.get(rid - 1)
            if prev and prev.get("meta"):
                rec["meta"] = json.loads(json.dumps(prev["meta"]))
                continue
        full = " ".join([
            rec.get("title", ""),
            *(rec.get("ingredients") or []),
            *(rec.get("steps") or []),
        ])
        proteins = detect_proteins(full)
        tags = proteins or ["vegetarien"]
        rec["meta"] = make_meta(15, 30, 6, None, None, "facile", tags)

    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    n_with_meta = sum(
        1 for r in recipes
        if r.get("meta") and any(
            r["meta"].get(k) is not None
            for k in ("prepMinutes", "cookMinutes", "servings", "yieldCount", "difficulty")
        )
    )
    print(f"Recipes processed: {len(recipes)}")
    print(f"Recipes with meta: {n_with_meta}")


if __name__ == "__main__":
    main()
