"""Replace stub recipes (from batches 2, 5, 6) with refined transcriptions.

The first transcription pass left stub entries for ~59 photos in batches 2/5/6
(title + "Voir image source pour la recette complète"). This script:

1. Identifies which sourcePhotos are covered by the new tools/_split_*_recipes.jsonl
   files (these are the ones with refined transcriptions).
2. Removes any existing recipe whose notes reference one of those photos.
3. Compacts/renumbers IDs above the soup-batch starting point so we don't leave
   gaps in the middle of the file. Recipes outside the affected ID range
   (1..334) keep their original IDs.
4. Appends the refined recipes with new sequential IDs.
5. Rebuilds the "les soupes" category recipeIds list to match.

Run from new-app/: `python tools/replace_stub_recipes.py`
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
ORIGINAL_MAX_ID = 334  # IDs 1..334 are pre-BOOK1 recipes; preserve them


def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    categories = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))

    # Load all refined entries from _split_*_recipes.jsonl.
    refined_entries: list[dict] = []
    refined_photos: set[str] = set()
    for sf in sorted(TOOLS_DIR.glob("_split_*_recipes.jsonl")):
        for line_no, raw in enumerate(sf.read_text(encoding="utf-8").splitlines(), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"WARN: {sf.name}:{line_no} bad JSON ({e}); skipping")
                continue
            refined_entries.append(obj)
            if obj.get("sourcePhoto"):
                refined_photos.add(obj["sourcePhoto"])

    print(f"Refined entries loaded: {len(refined_entries)} from {len(refined_photos)} photos")

    # Drop stubs: any recipe whose notes references one of the refined photos.
    def mentions_refined(notes: str | None) -> bool:
        if not notes:
            return False
        for m in re.findall(r"BOOK1/(\d+_\d+)\.heic", notes):
            if m in refined_photos:
                return True
        return False

    kept_recipes = [r for r in recipes if not mentions_refined(r.get("notes"))]
    dropped = len(recipes) - len(kept_recipes)
    print(f"Stub recipes dropped: {dropped}")

    # Sort refined entries by sourcePhoto so IDs follow page order.
    refined_entries.sort(key=lambda e: e.get("sourcePhoto", ""))

    # Renumber: keep IDs 1..ORIGINAL_MAX_ID untouched; for everything above,
    # reassign sequentially starting at ORIGINAL_MAX_ID+1.
    pre_existing = [r for r in kept_recipes if r["id"] <= ORIGINAL_MAX_ID]
    above = [r for r in kept_recipes if r["id"] > ORIGINAL_MAX_ID]
    above.sort(key=lambda r: r["id"])  # preserve relative order

    # Append refined entries to the "above" group, preserving sourcePhoto order.
    next_id = ORIGINAL_MAX_ID + 1
    new_above: list[dict] = []
    id_remap: dict[int, int] = {}

    for r in above:
        old_id = r["id"]
        new_r = dict(r)
        new_r["id"] = next_id
        new_r["numberLabel"] = f"Recette nº {next_id}"
        new_above.append(new_r)
        id_remap[old_id] = next_id
        next_id += 1

    appended_ids: list[int] = []
    for entry in refined_entries:
        photo = entry.get("sourcePhoto") or ""
        title = (entry.get("title") or "").strip() or "Recette sans titre"
        ingredients = entry.get("ingredients") or []
        steps = entry.get("steps") or []
        extra_notes = (entry.get("notes") or "").strip()

        photo_ref = (
            f"Transcrit automatiquement depuis BOOK1/{photo}.heic — à vérifier "
            "(titre, quantités et étapes peuvent contenir des erreurs)."
        )
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
        new_above.append(recipe)
        appended_ids.append(next_id)
        next_id += 1

    new_recipes = pre_existing + new_above

    # Rebuild every category's recipeIds list:
    # - For the soup category, recompute from scratch using all IDs > ORIGINAL_MAX_ID
    #   (they all belong to soups by construction) plus any soup IDs <= ORIGINAL_MAX_ID
    #   that were already in the list.
    # - For all other categories, just remap IDs through `id_remap` (and drop any
    #   that no longer exist).
    soup_cat = next((c for c in categories if c["name"] == TARGET_CATEGORY), None)
    if soup_cat is None:
        raise SystemExit(f"category {TARGET_CATEGORY!r} not found")

    pre_soup_ids = [i for i in soup_cat["recipeIds"] if i <= ORIGINAL_MAX_ID]
    new_soup_ids_above = [r["id"] for r in new_above]
    soup_cat["recipeIds"] = pre_soup_ids + new_soup_ids_above

    for cat in categories:
        if cat["name"] == TARGET_CATEGORY:
            continue
        remapped: list[int] = []
        for i in cat["recipeIds"]:
            if i <= ORIGINAL_MAX_ID:
                remapped.append(i)
            elif i in id_remap:
                remapped.append(id_remap[i])
            # else: ID was a stub that got dropped; don't include.
        cat["recipeIds"] = remapped

    RECIPES_PATH.write_text(
        json.dumps(new_recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    CATEGORIES_PATH.write_text(
        json.dumps(categories, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Refined entries appended : {len(appended_ids)}")
    if appended_ids:
        print(f"  ID range               : {appended_ids[0]} .. {appended_ids[-1]}")
    print(f"Recipes total            : {len(new_recipes)}")
    print(f"  ID range above 334     : {ORIGINAL_MAX_ID + 1} .. {next_id - 1}")


if __name__ == "__main__":
    main()
