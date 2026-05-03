"""Phase 2: applies in-session estimated meta to recipes.json.

Overrides recipe.meta with judgment-based estimates for prep/cook/servings,
plus new fields: yield (count + unit), difficulty, tags. Each estimate was
made by reading the recipe text in-session, so quality varies with how clear
the source text is.

Re-runnable. Run from new-app/: `python tools/merge_meta_overrides.py`

Schema for meta after this pass:
    {
      "prepMinutes":  int | None,
      "cookMinutes":  int | None,
      "servings":     int | None,   # for people-portions
      "yieldCount":   int | None,   # for biscuits / muffins / pots / etc.
      "yieldUnit":    str | None,   # what yieldCount measures
      "difficulty":   "facile" | "moyen" | "difficile" | None,
      "tags":         [str, ...]
    }

Tag vocabulary (lowercase, slugged):
    rapide              total time <= 30 min
    long-mijotage       cook time >= 90 min
    sans-cuisson        no heat involved
    vegetarien          no meat / poultry / fish / seafood (eggs/dairy ok)
    sans-gluten         heuristic, conservative
    congelation         recipe explicitly mentions freezing well
    conserves           jarring / pickling / preserves
    festif              special occasion / holiday
    four / micro-ondes / mijoteuse  primary cooking method
    poulet / boeuf / porc / veau / agneau / poisson / fruits-de-mer / jambon
                        primary protein
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes.json"

# Tuple shape: (prep, cook, servings, yieldCount, yieldUnit, difficulty, [tags])
META: dict[int, tuple] = {
    # --- salades / hors-d'oeuvre ---
    1:  (10, None, 6, None, None, "facile", ["sans-cuisson"]),
    2:  (10, None, 6, None, None, "facile", ["sans-cuisson", "vegetarien"]),
    4:  (10, 15, 4, None, None, "facile", ["vegetarien"]),
    6:  (15, 10, 8, None, None, "facile", ["vegetarien", "congelation"]),
    7:  (15, None, 11, None, None, "facile", ["sans-cuisson", "vegetarien"]),
    8:  (15, None, 6, None, None, "facile", ["sans-cuisson"]),
    9:  (10, None, 6, None, None, "facile", ["sans-cuisson", "vegetarien"]),
    10: (10, 15, 4, None, None, "moyen", ["fruits-de-mer"]),
    12: (15, None, 4, None, None, "facile", ["sans-cuisson", "vegetarien"]),
    13: (10, 5, 6, None, None, "facile", ["fruits-de-mer", "rapide", "four"]),
    15: (15, 20, 6, None, None, "facile", ["vegetarien", "four"]),
    16: (20, None, 4, None, None, "facile", ["sans-cuisson", "vegetarien"]),
    35: (30, 10, 8, None, None, "moyen", ["fruits-de-mer", "congelation"]),
    39: (25, 5, 6, None, None, "moyen", ["jambon", "congelation"]),
    40: (10, 15, 6, None, None, "facile", ["vegetarien", "four"]),
    41: (5, 10, 4, None, None, "facile", ["vegetarien", "four", "festif", "rapide"]),
    45: (20, None, 8, None, None, "facile", ["sans-cuisson", "vegetarien"]),
    63: (10, 15, 8, None, None, "facile", ["porc", "congelation"]),
    91: (30, 25, 6, None, None, "moyen", ["boeuf", "four"]),
    94: (30, 5, 6, None, None, "facile", ["poulet"]),
    98: (15, 60, 6, None, None, "moyen", ["poulet", "four"]),
    101:(25, 30, 6, None, None, "facile", ["vegetarien", "four"]),
    104:(20, None, 6, None, None, "facile", ["poisson", "sans-cuisson"]),
    180:(20, 5, None, 3, "pots", "facile", ["vegetarien", "conserves"]),
    181:(30, 10, None, 3, "chopines", "moyen", ["vegetarien", "conserves"]),

    # --- soupes (originales) ---
    17: (15, 60, 6, None, None, "facile", ["vegetarien"]),
    18: (10, 30, 6, None, None, "facile", ["vegetarien"]),
    19: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    20: (15, 25, 6, None, None, "facile", ["poulet"]),
    21: (5, 90, 6, None, None, "facile", ["boeuf", "long-mijotage"]),
    22: (15, 90, 8, None, None, "moyen", ["vegetarien", "long-mijotage"]),
    23: (10, 30, 6, None, None, "facile", ["vegetarien"]),
    24: (15, 45, 6, None, None, "facile", ["vegetarien"]),
    25: (15, 25, 6, None, None, "facile", ["vegetarien"]),
    26: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    27: (10, 110, 8, None, None, "facile", ["poulet", "long-mijotage"]),
    28: (15, 120, 8, None, None, "facile", ["porc", "long-mijotage"]),
    29: (30, 20, 6, None, None, "moyen", ["vegetarien"]),
    30: (15, 25, 6, None, None, "facile", ["vegetarien"]),
    31: (15, 60, 6, None, None, "facile", ["vegetarien"]),
    32: (15, 30, 6, None, None, "facile", ["vegetarien"]),
    33: (15, 10, 6, None, None, "moyen", ["vegetarien"]),
    202:(15, 45, 6, None, None, "facile", ["vegetarien", "four"]),

    # --- mets principaux ---
    200:(15, 20, 6, 12, "crepes", "facile", ["vegetarien"]),
    5:  (10, 15, 4, None, None, "facile", ["fruits-de-mer"]),
    14: (10, 10, 4, None, None, "facile", ["jambon", "four", "rapide"]),
    36: (25, 45, 8, 36, "pains", "moyen", ["porc", "congelation"]),
    43: (10, 20, 4, None, None, "facile", ["vegetarien", "four"]),
    46: (20, 40, 8, None, None, "moyen", ["vegetarien", "four"]),
    48: (30, 30, 6, None, None, "moyen", ["fruits-de-mer", "four"]),
    50: (15, 80, 6, None, None, "facile", ["porc"]),
    51: (20, 20, 6, None, None, "moyen", ["boeuf"]),
    52: (15, 55, 4, None, None, "facile", ["poulet"]),
    54: (15, 90, 4, None, None, "facile", ["boeuf", "long-mijotage"]),
    55: (25, 80, 6, None, None, "moyen", ["veau"]),
    56: (5, 15, 4, None, None, "facile", ["boeuf", "rapide"]),
    57: (15, 60, 6, None, None, "facile", ["jambon", "four"]),
    58: (30, 40, 8, None, None, "moyen", ["poulet", "four"]),
    59: (30, 45, 6, None, None, "moyen", ["boeuf", "four"]),
    60: (25, 90, 6, None, None, "moyen", ["boeuf", "long-mijotage", "congelation"]),
    61: (10, 15, 2, None, None, "moyen", ["boeuf"]),
    62: (25, 20, 4, None, None, "moyen", ["veau"]),
    64: (15, 45, 4, None, None, "facile", ["porc", "four"]),
    65: (30, 35, 6, None, None, "moyen", ["boeuf", "four"]),
    66: (20, 110, 6, None, None, "moyen", ["boeuf", "long-mijotage"]),
    67: (15, 180, 6, None, None, "facile", ["boeuf", "long-mijotage"]),
    68: (10, 45, 6, None, None, "facile", ["boeuf", "four"]),
    69: (20, 60, 6, None, None, "moyen", ["poulet", "four"]),
    70: (15, 25, 4, None, None, "facile", ["boeuf"]),
    71: (20, 25, 6, None, None, "moyen", ["boeuf"]),
    72: (25, 50, 6, None, None, "moyen", ["porc", "boeuf", "four"]),
    73: (30, 60, 6, None, None, "moyen", ["porc"]),
    75: (15, 150, 6, None, None, "facile", ["boeuf", "long-mijotage"]),
    76: (15, 120, 6, None, None, "facile", ["boeuf", "four", "long-mijotage"]),
    77: (15, 50, 6, None, None, "facile", ["boeuf", "four"]),
    78: (15, 20, 6, None, None, "facile", ["boeuf"]),
    82: (10, 15, 4, None, None, "facile", ["rapide", "four"]),
    83: (20, 150, 6, None, None, "moyen", ["boeuf", "four", "long-mijotage"]),
    84: (15, 90, 4, None, None, "facile", ["poulet", "four", "long-mijotage"]),
    86: (20, 30, 6, None, None, "moyen", ["poulet", "four"]),
    89: (20, 40, 6, None, None, "facile", ["boeuf"]),
    90: (10, 20, 4, None, None, "facile", ["boeuf", "rapide"]),
    92: (15, 20, 6, None, None, "facile", ["porc"]),
    93: (25, 50, 4, None, None, "moyen", ["poulet", "four"]),
    96: (15, 30, 6, None, None, "facile", ["boeuf", "four"]),
    97: (15, 60, 4, None, None, "facile", ["porc"]),
    99: (10, 90, 8, None, None, "facile", ["poulet", "four", "long-mijotage"]),
    102:(20, 90, 6, None, None, "moyen", ["veau", "four", "long-mijotage"]),
    103:(15, 10, 4, None, None, "facile", ["poisson", "four", "rapide"]),
    203:(20, 60, 6, None, None, "facile", ["vegetarien", "four"]),
    209:(20, 20, None, 3, "pizzas", "moyen", ["vegetarien", "four"]),
    213:(20, 30, None, 36, "boulettes", "facile", ["boeuf", "four", "congelation"]),
    214:(20, 30, 4, None, None, "moyen", ["boeuf", "four"]),
    215:(15, 60, 6, None, None, "facile", ["porc", "four"]),
    216:(15, 25, 4, None, None, "facile", ["boeuf"]),
    217:(40, 30, 8, None, None, "difficile", ["fruits-de-mer"]),
    218:(20, 60, 6, None, None, "facile", ["porc", "four"]),
    221:(15, 90, 8, None, None, "facile", ["boeuf", "four", "long-mijotage"]),

    # --- biscuits ---
    105:(20, 15, None, 24, "biscuits", "moyen", ["vegetarien", "four"]),
    106:(15, 15, None, 30, "biscuits", "facile", ["vegetarien", "four"]),
    107:(15, 12, None, 36, "biscuits", "facile", ["vegetarien", "four"]),
    109:(20, 10, None, 36, "biscuits", "moyen", ["vegetarien", "four"]),
    111:(20, 20, None, 36, "biscuits", "facile", ["vegetarien", "four"]),
    112:(20, 15, None, 30, "biscuits", "facile", ["vegetarien", "four"]),
    113:(15, 10, None, 36, "biscuits", "moyen", ["vegetarien", "four", "congelation"]),
    114:(15, 15, None, 30, "biscuits", "facile", ["vegetarien", "four"]),
    115:(15, 15, None, 42, "biscuits", "facile", ["vegetarien", "four"]),
    116:(15, 15, None, 42, "biscuits", "facile", ["vegetarien", "four"]),
    117:(15, 15, None, 30, "biscuits", "facile", ["vegetarien", "four"]),

    # --- desserts (gateaux, puddings, etc.) ---
    80: (10, 30, 8, None, None, "facile", ["vegetarien", "four"]),
    81: (15, 40, 8, None, None, "facile", ["vegetarien", "four"]),
    110:(20, 15, None, 24, "bouchees", "moyen", ["vegetarien"]),
    118:(15, 35, 8, None, None, "facile", ["vegetarien", "four"]),
    120:(15, 40, 10, None, None, "facile", ["vegetarien", "four"]),
    121:(20, 60, 10, None, None, "moyen", ["vegetarien", "four"]),
    123:(20, 35, 10, None, None, "moyen", ["vegetarien", "four"]),
    124:(15, 40, 10, None, None, "facile", ["vegetarien", "four"]),
    125:(15, 30, 8, None, None, "facile", ["vegetarien", "four"]),
    126:(20, 35, 10, None, None, "facile", ["vegetarien", "four"]),
    127:(20, 45, 10, None, None, "moyen", ["vegetarien", "four"]),
    128:(15, 30, 8, None, None, "facile", ["vegetarien", "four"]),
    129:(15, 35, 10, None, None, "facile", ["vegetarien", "four"]),
    130:(15, 10, None, 24, "morceaux", "facile", ["vegetarien"]),
    131:(20, 30, 12, None, None, "moyen", ["vegetarien", "four"]),
    132:(15, 15, 12, None, None, "facile", ["vegetarien", "micro-ondes"]),
    133:(25, 30, 12, None, None, "moyen", ["vegetarien", "four"]),
    135:(45, 10, 10, None, None, "difficile", ["vegetarien", "four", "festif"]),
    136:(30, 40, 8, None, None, "moyen", ["vegetarien", "four"]),
    137:(30, 20, None, 24, "beignes", "moyen", ["vegetarien"]),
    138:(25, 45, 10, None, None, "moyen", ["vegetarien", "four"]),
    139:(20, 60, 12, None, None, "facile", ["vegetarien", "four"]),
    140:(25, 45, 10, None, None, "moyen", ["vegetarien", "four"]),
    141:(20, 60, 10, 2, "gateaux", "facile", ["vegetarien", "four"]),
    142:(20, 45, 10, None, None, "facile", ["vegetarien", "four"]),
    143:(20, None, 8, None, None, "facile", ["vegetarien", "sans-cuisson"]),
    144:(15, 40, 10, None, None, "facile", ["vegetarien", "four"]),
    145:(25, 45, 12, None, None, "moyen", ["vegetarien", "four"]),
    146:(25, 10, None, 24, "morceaux", "moyen", ["vegetarien", "four"]),
    147:(20, 35, 8, None, None, "facile", ["vegetarien", "four"]),
    149:(15, 10, None, 4, "tasses", "facile", ["vegetarien", "micro-ondes", "congelation"]),
    150:(20, 50, 8, None, None, "facile", ["vegetarien", "four"]),
    151:(20, None, 8, None, None, "facile", ["vegetarien", "sans-cuisson"]),
    152:(25, 30, 10, None, None, "moyen", ["vegetarien", "four"]),
    153:(10, 10, None, 1, "glacage", "facile", ["vegetarien"]),
    154:(30, 20, 10, None, None, "difficile", ["vegetarien", "four", "festif"]),
    155:(25, None, None, 1, "glacage", "moyen", ["vegetarien", "sans-cuisson"]),
    156:(25, 35, 10, None, None, "moyen", ["vegetarien", "four"]),
    157:(10, 10, None, 1, "garniture", "facile", ["vegetarien"]),
    158:(20, 20, 10, None, None, "facile", ["vegetarien", "four"]),
    159:(15, 35, 10, None, None, "facile", ["vegetarien", "four"]),
    191:(15, 10, None, 24, "carres", "facile", ["vegetarien"]),
    192:(15, 15, None, 18, "macarons", "facile", ["vegetarien", "four", "sans-gluten"]),
    193:(20, 20, None, 16, "carres", "facile", ["vegetarien", "four"]),
    194:(10, 5, None, 1, "garniture", "facile", ["vegetarien", "rapide"]),
    195:(10, 25, None, 24, "carres", "facile", ["vegetarien", "four"]),
    212:(20, 30, None, 12, "gaufres", "facile", ["vegetarien"]),
    235:(10, 10, None, 24, "morceaux", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    236:(15, 10, None, 24, "morceaux", "facile", ["vegetarien", "micro-ondes"]),

    # --- tartes ---
    88: (25, 45, 6, None, None, "moyen", ["poisson", "four"]),
    108:(25, 15, None, 24, "biscuits", "facile", ["vegetarien", "four"]),
    134:(25, 15, 10, None, None, "facile", ["vegetarien", "four"]),
    148:(20, 40, 8, None, None, "facile", ["vegetarien", "four"]),
    160:(20, None, None, 4, "abaisses", "facile", ["vegetarien"]),
    161:(15, 30, 8, None, None, "facile", ["vegetarien", "four"]),
    162:(15, 15, 8, None, None, "facile", ["vegetarien", "four"]),
    163:(15, None, 8, None, None, "facile", ["vegetarien", "sans-cuisson"]),
    164:(15, 40, 8, None, None, "facile", ["vegetarien", "four"]),
    165:(10, 15, 8, None, None, "facile", ["vegetarien"]),
    166:(15, 20, 8, None, None, "facile", ["vegetarien", "four"]),
    167:(15, 70, 8, None, None, "facile", ["vegetarien", "four"]),
    168:(15, 40, 8, None, None, "facile", ["vegetarien", "four"]),
    169:(10, 25, 8, None, None, "facile", ["vegetarien", "four"]),
    170:(20, 40, 8, 2, "tartes", "facile", ["vegetarien", "four"]),
    171:(15, 20, 8, None, None, "facile", ["vegetarien", "four"]),
    172:(25, 20, 8, None, None, "moyen", ["vegetarien", "four"]),
    173:(20, 15, 8, None, None, "facile", ["vegetarien"]),
    174:(20, None, 8, None, None, "facile", ["vegetarien", "sans-cuisson"]),
    175:(15, 40, 8, None, None, "facile", ["vegetarien", "four"]),
    176:(20, 45, 8, None, None, "facile", ["vegetarien", "four"]),
    177:(10, 40, 8, None, None, "facile", ["vegetarien", "four"]),
    178:(25, 20, 8, None, None, "moyen", ["vegetarien", "four"]),

    # --- sauces ---
    11: (5, None, 4, None, None, "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    44: (5, None, None, 2, "tasses", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    47: (5, 10, None, 2, "tasses", "facile", ["vegetarien", "rapide"]),
    49: (15, None, None, 2, "tasses", "moyen", ["sans-cuisson", "vegetarien"]),
    53: (10, 30, None, 4, "tasses", "facile", ["vegetarien"]),
    79: (10, None, None, 1, "tasses", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    100:(5, 10, None, 2, "tasses", "facile", ["vegetarien", "rapide"]),
    122:(10, 5, None, 2, "tasses", "facile", ["vegetarien", "rapide"]),
    179:(45, 70, None, 8, "pots", "difficile", ["vegetarien", "conserves"]),
    183:(5, 10, None, 1, "tasses", "facile", ["vegetarien", "rapide"]),
    184:(5, None, None, 1, "tasses", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    185:(5, None, None, 1, "tasses", "facile", ["vegetarien", "rapide"]),
    186:(10, 20, None, 3, "tasses", "facile", ["vegetarien"]),
    187:(5, 5, None, 2, "tasses", "facile", ["vegetarien", "rapide"]),
    188:(10, 10, None, 1, "tasses", "facile", ["vegetarien", "rapide"]),
    189:(10, 10, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    190:(10, 10, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    219:(5, None, None, 1, "tasses", "facile", ["sans-cuisson", "rapide"]),
    220:(20, 180, 10, None, None, "moyen", ["boeuf", "four", "long-mijotage", "congelation"]),
    223:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    224:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    225:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    226:(15, 5, None, 2, "tasses", "facile", ["vegetarien", "micro-ondes"]),
    227:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    228:(10, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    229:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    230:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    231:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    232:(10, 10, None, 2, "tasses", "facile", ["vegetarien", "rapide"]),
    233:(5, 5, None, 1, "tasses", "facile", ["vegetarien", "micro-ondes", "rapide"]),
    234:(5, 10, None, 1, "tasses", "facile", ["vegetarien", "rapide"]),

    # --- epices ---
    74: (5, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    87: (5, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    95: (20, 240, 10, None, None, "moyen", ["boeuf", "long-mijotage"]),
    182:(20, None, None, 2, "pots", "facile", ["sans-cuisson", "vegetarien", "conserves"]),
    196:(15, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    197:(5, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    198:(10, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),
    199:(5, None, None, 1, "pot", "facile", ["sans-cuisson", "vegetarien", "rapide"]),

    # --- drinks ---
    201:(15, None, 12, None, None, "facile", ["vegetarien", "sans-cuisson"]),
    204:(10, 5, 8, None, None, "facile", ["vegetarien", "rapide"]),
    205:(10, None, 4, None, None, "facile", ["vegetarien", "sans-cuisson", "rapide"]),
    206:(15, None, 12, None, None, "facile", ["vegetarien", "congelation"]),
    207:(10, None, 8, None, None, "facile", ["vegetarien", "sans-cuisson", "rapide"]),

    # --- brunch / pains / divers (originaux) ---
    3:  (30, 25, 10, 2, "brioches", "difficile", ["vegetarien", "four"]),
    34: (10, 15, 8, None, None, "facile", ["vegetarien", "four", "rapide"]),
    37: (30, None, 10, None, None, "facile", ["vegetarien", "sans-cuisson", "festif"]),
    38: (60, None, 10, None, None, "difficile", ["sans-cuisson", "festif"]),
    42: (25, None, None, 1, "pates", "facile", ["vegetarien"]),
    85: (20, 30, 6, None, None, "facile", ["jambon", "four"]),
    119:(15, 20, 6, 12, "grands-peres", "facile", ["vegetarien"]),
    208:(10, 200, 10, None, None, "facile", ["vegetarien", "long-mijotage"]),
    210:(20, 20, None, 18, "brioches", "moyen", ["vegetarien", "four"]),
    211:(10, 180, 10, None, None, "facile", ["vegetarien", "long-mijotage"]),
    222:(20, 30, 6, None, None, "facile", ["boeuf", "four"]),

    # --- nouvelles soupes (BOOK1, IDs 237-316) ---
    237:(15, 30, 4, None, None, "facile", ["vegetarien"]),
    238:(15, 25, 6, None, None, "moyen", ["fruits-de-mer"]),
    239:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    240:(15, 30, 4, None, None, "facile", ["vegetarien"]),
    241:(15, 20, 6, None, None, "facile", ["vegetarien"]),
    242:(20, 30, 6, None, None, "facile", ["vegetarien"]),
    243:(20, 105, 8, None, None, "moyen", ["vegetarien", "long-mijotage"]),
    244:(15, 20, 8, None, None, "facile", ["poulet", "rapide"]),
    245:(20, 90, 7, None, None, "moyen", ["vegetarien", "long-mijotage"]),
    246:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    247:(20, 105, 12, None, None, "facile", ["poulet", "long-mijotage"]),
    248:(15, 120, 12, None, None, "facile", ["poulet", "long-mijotage"]),
    249:(15, 30, 6, None, None, "facile", ["poulet"]),
    250:(20, 40, 6, None, None, "moyen", ["vegetarien"]),
    251:(20, 105, 8, None, None, "facile", ["vegetarien", "long-mijotage"]),
    252:(20, 30, 6, None, None, "moyen", ["vegetarien"]),
    253:(20, 105, 8, None, None, "moyen", ["boeuf", "long-mijotage"]),
    254:(20, 60, 8, None, None, "facile", ["poulet"]),
    255:(15, 60, 6, None, None, "facile", ["boeuf"]),
    256:(15, 90, 6, None, None, "facile", ["poulet", "long-mijotage", "congelation"]),
    257:(15, 60, 6, None, None, "moyen", ["vegetarien", "four"]),
    258:(15, 60, 6, None, None, "facile", ["poulet"]),
    259:(45, 120, 12, None, None, "difficile", ["boeuf", "porc", "poulet", "long-mijotage"]),
    260:(30, 75, 8, None, None, "difficile", ["poulet"]),
    261:(20, 60, 8, None, None, "facile", ["poulet"]),
    262:(20, 105, 8, None, None, "facile", ["poulet", "long-mijotage"]),
    263:(20, 40, 6, None, None, "moyen", ["poisson", "fruits-de-mer"]),
    264:(15, 45, 6, None, None, "facile", ["jambon"]),
    265:(20, 30, 4, None, None, "moyen", ["poulet"]),
    266:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    267:(25, 70, 8, None, None, "moyen", ["boeuf", "poulet"]),
    268:(20, 60, 8, None, None, "facile", ["jambon"]),
    269:(20, 120, 10, None, None, "facile", ["jambon", "long-mijotage"]),
    270:(10, 30, 6, None, None, "facile", ["vegetarien"]),
    271:(15, 40, 6, None, None, "facile", ["vegetarien"]),
    272:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    273:(20, 30, 6, None, None, "moyen", ["fruits-de-mer"]),
    274:(20, 40, 6, None, None, "moyen", ["vegetarien"]),
    275:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    276:(15, 30, 6, None, None, "moyen", ["vegetarien"]),
    277:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    278:(30, 65, 6, None, None, "difficile", ["poisson", "fruits-de-mer"]),
    279:(20, 30, 6, None, None, "facile", ["poulet"]),
    280:(20, 30, 6, None, None, "moyen", ["vegetarien"]),
    281:(20, 35, 6, None, None, "moyen", ["vegetarien"]),
    282:(10, 10, 4, None, None, "facile", ["vegetarien", "rapide"]),
    283:(15, 20, 6, None, None, "facile", ["vegetarien"]),
    284:(15, 20, 6, None, None, "moyen", ["vegetarien"]),
    285:(15, 15, 6, None, None, "facile", ["vegetarien"]),
    286:(15, 25, 6, None, None, "facile", ["vegetarien"]),
    287:(15, 20, 6, None, None, "facile", ["vegetarien"]),
    288:(15, 35, 6, None, None, "facile", ["vegetarien"]),
    289:(20, 45, 4, None, None, "moyen", ["fruits-de-mer"]),
    290:(15, 70, 8, None, None, "facile", ["poulet"]),
    291:(20, 60, 8, None, None, "facile", ["poulet"]),
    292:(15, 40, 6, None, None, "facile", ["vegetarien"]),
    293:(15, 50, 6, None, None, "facile", ["vegetarien"]),
    294:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    295:(10, 30, 6, None, None, "facile", ["vegetarien"]),
    296:(15, 35, 6, None, None, "moyen", ["vegetarien"]),
    297:(20, 25, 4, None, None, "facile", ["poulet"]),
    298:(15, 90, 8, None, None, "facile", ["jambon", "long-mijotage"]),
    299:(20, 45, 6, None, None, "facile", ["vegetarien"]),
    300:(15, 45, 6, None, None, "facile", ["poulet"]),
    301:(20, 45, 6, None, None, "moyen", ["poisson", "fruits-de-mer"]),
    302:(30, 75, 8, None, None, "moyen", ["boeuf", "veau"]),
    303:(15, 60, 6, None, None, "facile", ["boeuf"]),
    304:(15, 150, 8, None, None, "facile", ["porc", "long-mijotage"]),
    305:(20, 60, 6, None, None, "facile", ["poulet"]),
    306:(20, 15, 6, None, None, "moyen", ["vegetarien"]),
    307:(15, 20, 4, None, None, "facile", ["poulet"]),
    308:(20, 45, 6, None, None, "moyen", ["vegetarien"]),
    309:(20, 30, 6, None, None, "moyen", ["boeuf"]),
    310:(15, 90, 6, None, None, "moyen", ["agneau", "long-mijotage"]),
    311:(15, 60, 6, None, None, "facile", ["porc"]),
    312:(20, 30, 4, None, None, "moyen", ["vegetarien"]),
    313:(15, 90, 6, None, None, "facile", ["boeuf", "long-mijotage"]),
    314:(25, 30, 4, None, None, "moyen", ["fruits-de-mer"]),
    315:(20, 30, 6, None, None, "facile", ["vegetarien"]),
    316:(20, 150, 8, None, None, "facile", ["porc", "long-mijotage"]),

    # --- BOOK1 sideways pages (incomplete, low-confidence) ---
    317:(None, None, None, None, None, None, []),
    318:(None, None, None, None, None, None, []),
    319:(None, None, None, None, None, None, []),
    320:(15, 30, 4, None, None, "facile", ["vegetarien"]),
    321:(15, 45, 6, None, None, "facile", ["porc"]),
    322:(None, None, None, None, None, None, []),
    323:(None, None, None, None, None, None, []),
    324:(15, 20, 6, None, None, "moyen", ["fruits-de-mer"]),
    325:(None, None, None, None, None, None, []),
    326:(20, 60, 6, None, None, "facile", ["poulet"]),
    327:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    328:(15, 25, 6, None, None, "facile", ["vegetarien"]),
    329:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    330:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    331:(15, 50, 6, None, None, "facile", ["vegetarien"]),
    332:(15, 30, 6, None, None, "facile", ["vegetarien"]),
    333:(None, None, None, None, None, None, []),
    334:(None, None, None, None, None, None, []),
}


def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    n_total = 0
    n_with_meta = 0
    missing_ids = []
    for r in recipes:
        rid = r["id"]
        n_total += 1
        if rid not in META:
            missing_ids.append(rid)
            continue
        prep, cook, serv, yc, yu, diff, tags = META[rid]
        r["meta"] = {
            "prepMinutes": prep,
            "cookMinutes": cook,
            "servings": serv,
            "yieldCount": yc,
            "yieldUnit": yu,
            "difficulty": diff,
            "tags": list(tags) if tags else [],
        }
        if any(v is not None for v in (prep, cook, serv, yc, diff)) or tags:
            n_with_meta += 1
    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Recipes processed: {n_total}")
    print(f"Recipes with meta: {n_with_meta}")
    if missing_ids:
        print(f"Missing meta for {len(missing_ids)} ids: {missing_ids[:20]}")


if __name__ == "__main__":
    main()
