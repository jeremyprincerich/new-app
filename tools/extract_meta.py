"""Regex pass that fills recipe.meta = { servings, cookMinutes, prepMinutes }
on each recipe in recipes.json.

- servings   : extracted from title/ingredients/steps if patterns like
               "(4 pers)", "pour 6", "donne 12 biscuits" appear.
- cookMinutes: sum of duration tokens found in steps text. Caps at 6 h.
- prepMinutes: left null — there is no signal in the text.

Idempotent: rewrites meta on every run. Run from new-app/.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes.json"

# --- servings -------------------------------------------------------------
# Match French "personnes", "pers", "portions", "donne 12 biscuits", "pour 6".
# Order matters: more specific patterns first.
SERVING_PATTERNS = [
    re.compile(r"\((\d+)\s*(?:à|a|-)\s*(\d+)\s*pers", re.IGNORECASE),  # (6 à 8 pers)
    re.compile(r"\((\d+)\s*pers", re.IGNORECASE),                        # (4 pers)
    re.compile(r"\b(\d+)\s*(?:à|a|-)\s*(\d+)\s*pers(?:onnes?)?\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s*pers(?:onnes?)?\b", re.IGNORECASE),
    re.compile(r"\bpour\s*(\d+)\s*(?:pers(?:onnes?)?|convives?)\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s*portions?\b", re.IGNORECASE),
    re.compile(r"\bdonne\s+(?:environ\s+)?(\d+)\s+(?:biscuits|muffins|tartelettes|crêpes|pancakes|galettes|boulettes|portions)\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s+biscuits\b", re.IGNORECASE),
]


def extract_servings(haystacks: list[str]) -> int | None:
    text = " ".join(h for h in haystacks if h)
    for pat in SERVING_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        groups = [g for g in m.groups() if g is not None]
        if len(groups) == 2:
            try:
                lo, hi = int(groups[0]), int(groups[1])
                # average for ranges, snap to int
                return (lo + hi) // 2
            except ValueError:
                continue
        try:
            n = int(groups[0])
        except ValueError:
            continue
        if 1 <= n <= 60:
            return n
    return None


# --- cooking time ---------------------------------------------------------
# French unit tokens: heure(s) / h, minute(s) / min / mn.
# Patterns to recognize (case-insensitive):
#   "30 min", "30 minutes", "1 h 30", "1h30", "2 heures", "1 h"
#   "1 1/2 h", "1/2 heure"
# Also catches ranges like "2 à 3 h" — takes the max.

NUM = r"(?:\d+(?:[.,]\d+)?(?:\s+\d/\d)?|\d/\d)"

# duration patterns; each yields total minutes
RANGE_HOUR_MIN = re.compile(
    rf"({NUM})\s*(?:à|a|-|–|—)\s*({NUM})\s*(?:h|heures?|hrs?)",
    re.IGNORECASE,
)
RANGE_MIN = re.compile(
    rf"({NUM})\s*(?:à|a|-|–|—)\s*({NUM})\s*(?:min(?:utes?)?|mn)\b",
    re.IGNORECASE,
)
H_AND_MIN = re.compile(rf"({NUM})\s*h(?:eures?)?\s*({NUM})\s*(?:min(?:utes?)?|mn)?\b", re.IGNORECASE)
H_ONLY = re.compile(rf"({NUM})\s*(?:h|heures?|hrs?)\b", re.IGNORECASE)
MIN_ONLY = re.compile(rf"({NUM})\s*(?:min(?:utes?)?|mn)\b", re.IGNORECASE)


def parse_num(s: str) -> float:
    s = s.strip().replace(",", ".")
    # mixed fraction: "1 1/2"
    m = re.fullmatch(r"(\d+)\s+(\d)/(\d)", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    # plain fraction: "1/2"
    m = re.fullmatch(r"(\d)/(\d)", s)
    if m:
        return int(m.group(1)) / int(m.group(2))
    try:
        return float(s)
    except ValueError:
        return 0.0


def extract_cook_minutes(steps_text: str) -> int | None:
    """Find the longest single duration mentioned in step text.

    Using max (not sum) is more robust — recipes often list overlapping
    durations ("mijoter 30 min, écumer toutes les 5 min") and summing
    them inflates badly.
    """
    if not steps_text:
        return None
    candidates: list[float] = []  # in minutes

    # Process in priority order. Each match consumes its span so we don't double-count.
    consumed = [False] * len(steps_text)

    def consume(span):
        for i in range(*span):
            if i < len(consumed):
                consumed[i] = True

    def free(span):
        return all(not consumed[i] for i in range(*span) if i < len(consumed))

    for pat, fn in [
        (H_AND_MIN, lambda m: parse_num(m.group(1)) * 60 + parse_num(m.group(2))),
        (RANGE_HOUR_MIN, lambda m: parse_num(m.group(2)) * 60),
        (RANGE_MIN, lambda m: parse_num(m.group(2))),
        (H_ONLY, lambda m: parse_num(m.group(1)) * 60),
        (MIN_ONLY, lambda m: parse_num(m.group(1))),
    ]:
        for m in pat.finditer(steps_text):
            if not free(m.span()):
                continue
            mins = fn(m)
            if 1 <= mins <= 360:  # ignore 0 and >6h
                candidates.append(mins)
                consume(m.span())

    if not candidates:
        return None
    # Round to nearest 5 min.
    longest = max(candidates)
    return int(round(longest / 5) * 5) or 5


# --- main -----------------------------------------------------------------
def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))

    n_serv = 0
    n_cook = 0
    for r in recipes:
        title = r.get("title", "") or ""
        ingredients = r.get("ingredients", []) or []
        steps = r.get("steps", []) or []
        notes = r.get("notes", "") or ""

        servings = extract_servings([title, *ingredients, *steps, notes])
        cook = extract_cook_minutes(" \n ".join(steps + ingredients))

        meta = {
            "servings": servings,
            "cookMinutes": cook,
            "prepMinutes": None,
        }
        r["meta"] = meta
        if servings is not None:
            n_serv += 1
        if cook is not None:
            n_cook += 1

    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    total = len(recipes)
    print(f"Recipes: {total}")
    print(f"  servings    extracted: {n_serv} ({n_serv/total*100:.0f}%)")
    print(f"  cookMinutes extracted: {n_cook} ({n_cook/total*100:.0f}%)")


if __name__ == "__main__":
    main()
