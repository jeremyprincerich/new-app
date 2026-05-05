"""Generate db/recipes_seed.sql from recipes.json.

Run after editing recipes.json to refresh the seed file. The output is a
single SQL batch with one INSERT per recipe, idempotent via ON CONFLICT.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/JonathanPrince/.claude/projects/BOOK/new-app")
SRC = ROOT / "recipes.json"
OUT = ROOT / "db/recipes_seed.sql"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    with open(SRC, encoding="utf-8") as f:
        recipes = json.load(f)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("-- Auto-generated from recipes.json by tools/generate_recipes_seed.py\n")
        f.write(f"-- Recipes: {len(recipes)}\n")
        f.write("-- Run AFTER schema.sql. Idempotent: re-running updates existing rows.\n\n")
        f.write("begin;\n\n")
        for r in recipes:
            rid = r["id"]
            # JSON-encode the full record. Postgres expects a literal string;
            # double single-quotes to escape, and use the E'...' escape syntax
            # for any backslashes — but the safest approach is to use jsonb_build
            # via a parameterized query. For a one-shot SQL file we use the
            # simpler `'...'::jsonb` literal with single-quote escaping.
            payload = json.dumps(r, ensure_ascii=False, separators=(",", ":"))
            payload_escaped = payload.replace("'", "''")
            f.write(
                f"insert into public.recipes (id, data) values ({rid}, '{payload_escaped}'::jsonb)\n"
                f"  on conflict (id) do update set data = excluded.data, updated_at = now();\n"
            )
        f.write("\ncommit;\n")

    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT}  ({len(recipes)} recipes, {size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
