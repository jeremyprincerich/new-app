"""Merge tools/_batch_*_recipes.jsonl into recipes.json + categories.json.

- Reads every `tools/_batch_*_recipes.jsonl` produced by the transcription pass.
- Sorts entries by `sourcePhoto` (chronological page order from the cookbook).
- Assigns sequential IDs starting at max(existing id) + 1.
- Each new recipe gets:
    id, numberLabel ("Recette nº N"), title, ingredients, steps, notes, meta=nulls
  with the BOOK1 source photo recorded at the end of `notes`.
- Appends the new IDs to the "les soupes" category in categories.json.
- Idempotent-ish: skips entries whose sourcePhoto is already referenced in
  recipes.json (so re-running won't double-insert).

Run from new-app/: `python tools/merge_new_book1.py`
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes.json"
CATEGORIES_PATH = ROOT / "categories.json"
TOOLS_DIR = ROOT / "tools"

TARGET_CATEGORY = "les soupes"


def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    categories = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))

    # Find which photos are already referenced.
    already_referenced: set[str] = set()
    for r in recipes:
        notes = r.get("notes") or ""
        for m in re.findall(r"BOOK1/(\d+_\d+)\.heic", notes):
            already_referenced.add(m)

    # Collect entries from all batch JSONL files.
    new_entries: list[dict] = []
    batch_files = sorted(TOOLS_DIR.glob("_batch_*_recipes.jsonl"))
    for bf in batch_files:
        for line_no, raw in enumerate(bf.read_text(encoding="utf-8").splitlines(), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"WARN: {bf.name}:{line_no} not valid JSON ({e}); skipping")
                continue
            new_entries.append(obj)

    # Sort by sourcePhoto so IDs follow page order in the cookbook.
    new_entries.sort(key=lambda e: e.get("sourcePhoto", ""))

    next_id = max((r["id"] for r in recipes), default=0) + 1
    appended_ids: list[int] = []
    skipped = 0

    # Snapshot what was already in recipes.json BEFORE this run.
    # We dedup against that snapshot only — multi-recipe pages legitimately
    # produce multiple JSONL entries with the same sourcePhoto, and they all
    # belong as separate recipes.
    pre_existing = set(already_referenced)

    for entry in new_entries:
        photo = entry.get("sourcePhoto") or ""
        if photo and photo in pre_existing:
            skipped += 1
            continue

        title = (entry.get("title") or "").strip() or "Recette sans titre"
        ingredients = entry.get("ingredients") or []
        steps = entry.get("steps") or []
        extra_notes = (entry.get("notes") or "").strip()

        photo_ref = f"Transcrit automatiquement depuis BOOK1/{photo}.heic — à vérifier (titre, quantités et étapes peuvent contenir des erreurs)."
        notes = photo_ref if not extra_notes else f"{photo_ref}\n{extra_notes}"

        recipe = {
            "id": next_id,
            "numberLabel": f"Recette nº {next_id}",
            "title": title,
            "ingredients": ingredients,
            "steps": steps,
            "notes": notes,
            "meta": {
                "servings": None,
                "cookMinutes": None,
                "prepMinutes": None,
            },
        }
        recipes.append(recipe)
        appended_ids.append(next_id)
        next_id += 1

    # Add new IDs to the target category.
    target = next((c for c in categories if c["name"] == TARGET_CATEGORY), None)
    if target is None:
        raise SystemExit(f"category {TARGET_CATEGORY!r} not found in categories.json")
    existing = set(target["recipeIds"])
    for new_id in appended_ids:
        if new_id not in existing:
            target["recipeIds"].append(new_id)
            existing.add(new_id)

    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    CATEGORIES_PATH.write_text(
        json.dumps(categories, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Batch files processed : {len(batch_files)}")
    print(f"Entries read          : {len(new_entries)}")
    print(f"Skipped (already in)  : {skipped}")
    print(f"Recipes appended      : {len(appended_ids)}")
    if appended_ids:
        print(f"  ID range            : {appended_ids[0]} .. {appended_ids[-1]}")
    print(f"Total recipes now     : {len(recipes)}")


if __name__ == "__main__":
    main()
