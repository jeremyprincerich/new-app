"""Phase 1 nutrient estimator for BOOK recipes.

Inputs:
  - BOOK/new-app/recipes.json
  - BOS/workspace/food/exports/food_app_v1.sqlite      (slim, FTS5)
  - BOS/workspace/food/db/food_meta.db                 (canonical fallback)

Outputs (under BOOK/new-app/tools/output/):
  - recipes_nutrition_phase1.json
  - unmatched_phrases.csv
  - low_confidence_recipes.csv
  - phase1_run.log
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

ROOT = Path("C:/Users/JonathanPrince/.claude/projects")
RECIPES_JSON  = ROOT / "BOOK/new-app/recipes.json"
SLIM_DB       = ROOT / "BOS/workspace/food/exports/food_app_v1.sqlite"
CANONICAL_DB  = ROOT / "BOS/workspace/food/db/food_meta.db"
OUT_DIR       = ROOT / "BOOK/new-app/tools/output"


# ============================================================================
# 1. UNIT + DENSITY TABLES
# ============================================================================
# Volumes are normalized to milliliters first, then to grams via density.
# Quebec/French units accepted in addition to metric.
ML_PER_UNIT: dict[str, float] = {
    # weight pseudo-units (handled separately) — kept here as None markers
    # volume
    "ml": 1.0, "millilitre": 1.0, "millilitres": 1.0,
    "l": 1000.0, "litre": 1000.0, "litres": 1000.0,
    "tasse": 250.0, "tasses": 250.0, "t": 250.0,         # Canadian metric cup
    "c_soupe": 15.0,                                      # tablespoon
    "c_the":   5.0,                                       # teaspoon
    "pincee":  0.5,                                       # ~0.5ml
}

GRAMS_PER_UNIT: dict[str, float] = {
    "g": 1.0, "gr": 1.0, "gramme": 1.0, "grammes": 1.0,
    "kg": 1000.0,
    "lb": 453.592, "lbs": 453.592, "livre": 453.592, "livres": 453.592,
    "oz": 28.3495, "once": 28.3495, "onces": 28.3495,
}

# Counts → typical grams per item (medium / standard).
# These are coarse defaults; food-specific overrides applied in convert_to_grams.
COUNT_DEFAULTS: dict[str, float] = {
    "oeuf": 50.0,         # large egg
    "gousse": 5.0,        # garlic clove
    "branche": 40.0,      # celery stalk
    "tranche": 25.0,      # standard slice (bread, cheese, ham)
    "paquet": 250.0,      # vague — flagged low confidence
    "boite": 400.0,       # standard can
    "sachet": 30.0,       # spice/yeast packet
    "feuille": 5.0,       # bay leaf, etc.
    "pincee": 0.5,
}

# Density (g/ml) by canonical "food kind" — used when the unit is volumetric
# and we need to convert to grams. Applied via keyword match on the phrase.
DENSITY_BY_KEYWORD: list[tuple[str, float]] = [
    # exact-y matches first
    ("huile",            0.92),
    ("oil",              0.92),
    ("beurre",           0.95),
    ("butter",           0.95),
    ("margarine",        0.95),
    ("shortening",       0.92),
    ("graisse",          0.92),
    ("saindoux",         0.92),
    ("lard",             0.92),
    ("miel",             1.42),
    ("honey",            1.42),
    ("sirop",            1.32),
    ("syrup",            1.32),
    ("melasse",          1.45),
    ("molasses",         1.45),
    ("creme",            1.01),
    ("cream",            1.01),
    ("lait",             1.03),
    ("milk",             1.03),
    ("yogourt",          1.03),
    ("yogurt",           1.03),
    ("yaourt",           1.03),
    ("eau",              1.00),
    ("water",            1.00),
    ("vinaigre",         1.01),
    ("vinegar",          1.01),
    ("vin",              0.99),
    ("wine",             0.99),
    ("bouillon",         1.00),
    ("broth",            1.00),
    ("jus",              1.04),
    ("juice",            1.04),
    ("sauce soya",       1.20),
    ("sauce soja",       1.20),
    ("soy sauce",        1.20),
    ("ketchup",          1.10),
    ("mayonnaise",       0.91),
    ("mayo",             0.91),
    ("moutarde",         1.05),
    ("mustard",          1.05),
    ("farine",           0.55),       # all-purpose flour, packed-ish
    ("flour",            0.55),
    ("sucre",            0.85),       # granulated sugar
    ("sugar",            0.85),
    ("cassonade",        0.93),       # brown sugar packed
    ("brown sugar",      0.93),
    ("poudre",           0.85),       # powders generic (baking powder/soda)
    ("baking",           0.85),
    ("sel",              1.20),       # table salt
    ("salt",             1.20),
    ("riz cuit",         0.78),
    ("cooked rice",      0.78),
    ("riz",              0.80),       # raw rice (light overestimate vs ~0.75)
    ("rice",             0.80),
    ("flocon",           0.34),       # oats
    ("avoine",           0.34),
    ("oats",             0.34),
    ("fromage rape",     0.46),
    ("shredded cheese",  0.46),
    ("fromage",          0.96),       # block cheese (dense)
    ("cheese",           0.96),
    ("legume",           0.55),       # diced veggies generic
    ("oignon",           0.60),       # diced onion
    ("onion",            0.60),
    ("celeri",           0.40),
    ("celery",           0.40),
    ("carotte",          0.55),
    ("carrot",           0.55),
    ("tomate",           0.95),
    ("tomato",           0.95),
    ("champignon",       0.50),
    ("mushroom",         0.50),
    ("noix",             0.50),       # chopped nuts
    ("nut",              0.50),
    ("amande",           0.55),
    ("almond",           0.55),
    ("raisin sec",       0.60),
    ("raisin",           0.65),
    ("chocolat",         0.62),       # chocolate chips
    ("chocolate",        0.62),
    ("cacao",            0.50),
    ("cocoa",            0.50),
]

DEFAULT_DENSITY = 0.70  # generic solid; flagged low confidence

# Per-food count overrides (when "1 X" appears, weight in grams).
COUNT_OVERRIDES: list[tuple[str, dict[str, float]]] = [
    ("oeuf",         {"oeuf": 50.0, "unit": 50.0}),
    ("egg",          {"oeuf": 50.0, "unit": 50.0}),
    ("oignon",       {"unit": 110.0}),
    ("onion",        {"unit": 110.0}),
    ("ail",          {"gousse": 5.0, "unit": 5.0}),
    ("garlic",       {"gousse": 5.0, "unit": 5.0}),
    ("citron",       {"unit": 90.0}),
    ("lemon",        {"unit": 90.0}),
    ("lime",         {"unit": 65.0}),
    ("tomate",       {"unit": 130.0}),
    ("tomato",       {"unit": 130.0}),
    ("pomme",        {"unit": 180.0}),
    ("apple",        {"unit": 180.0}),
    ("banane",       {"unit": 120.0}),
    ("banana",       {"unit": 120.0}),
    ("carotte",      {"unit": 60.0}),
    ("carrot",       {"unit": 60.0}),
    ("celeri",       {"branche": 40.0, "unit": 200.0}),
    ("celery",       {"branche": 40.0}),
    ("brocoli",      {"unit": 600.0}),     # whole head
    ("broccoli",     {"unit": 600.0}),
    ("chou-fleur",   {"unit": 800.0}),
    ("cauliflower",  {"unit": 800.0}),
    ("courge",       {"unit": 1000.0}),
    ("squash",       {"unit": 1000.0}),
    ("courgette",    {"unit": 200.0}),
    ("zucchini",     {"unit": 200.0}),
    ("concombre",    {"unit": 300.0}),
    ("cucumber",     {"unit": 300.0}),
    ("poivron",      {"unit": 150.0}),
    ("piment",       {"unit": 150.0}),
    ("pepper",       {"unit": 150.0}),
    ("patate douce", {"unit": 200.0}),
    ("sweet potato", {"unit": 200.0}),
    ("patate",       {"unit": 175.0}),
    ("potato",       {"unit": 175.0}),
    ("pomme de terre",{"unit": 175.0}),
    ("avocat",       {"unit": 200.0}),
    ("avocado",      {"unit": 200.0}),
    ("orange",       {"unit": 130.0}),
    ("poire",        {"unit": 180.0}),
    ("pear",         {"unit": 180.0}),
    ("navet",        {"unit": 250.0}),
    ("turnip",       {"unit": 250.0}),
    ("champignon",   {"unit": 18.0}),       # one cremini ~18g
    ("mushroom",     {"unit": 18.0}),
    ("echalote",     {"unit": 30.0}),
    ("shallot",      {"unit": 30.0}),
    ("brie",         {"unit": 250.0}),     # small wheel
    ("camembert",    {"unit": 250.0}),
    ("croute",       {"unit": 150.0}),     # one pie crust
    ("crust",        {"unit": 150.0}),
    ("croissant",    {"unit": 60.0}),
    ("muffin",       {"unit": 75.0}),
    ("melange",      {"unit": 85.0}),      # one packet (pudding/dressing mix)
    ("sachet",       {"unit": 30.0}),
    ("enveloppe",    {"unit": 30.0}),
    ("paquet",       {"unit": 250.0}),
    ("boite",        {"unit": 400.0}),
    ("pot",          {"unit": 250.0}),
    ("bouteille",    {"unit": 750.0}),     # generic bottle (wine/beer)
    ("biere",        {"unit": 355.0}),     # one beer can
]


# ============================================================================
# 2. FRENCH → CANONICAL ENGLISH PHRASE (curated, additive)
# ============================================================================
# Maps a stripped French food phrase to a USDA-style English query.
# Keys are normalized (lowercased, accents removed, punctuation light).
# Order matters: more specific keys checked first (longer first).
TRANSLATION: dict[str, str] = {
    # proteins
    "poulet":                       "chicken",
    "poulet desosse":               "chicken boneless",
    "poitrine de poulet":           "chicken breast",
    "ailes de poulet":              "chicken wings",
    "cuisse de poulet":             "chicken thigh",
    "boeuf":                        "beef ground",
    "boeuf hache":                  "beef ground",
    "porc":                         "pork",
    "porc hache":                   "pork ground",
    "jambon":                       "ham",
    "bacon":                        "bacon",
    "saucisse":                     "sausage",
    "saumon":                       "salmon",
    "thon":                         "tuna canned",
    "crevette":                     "shrimp",
    "crevettes":                    "shrimp",
    "petoncle":                     "scallops",
    "petoncles":                    "scallops",
    "oeuf":                         "egg whole",
    "oeufs":                        "egg whole",
    "œuf":                          "egg whole",
    "blanc d'oeuf":                 "egg white",
    "jaune d'oeuf":                 "egg yolk",
    # dairy
    "lait":                         "milk whole",
    "lait 2%":                      "milk 2%",
    "lait ecreme":                  "milk skim",
    "creme":                        "cream heavy",
    "creme 35%":                    "cream heavy",
    "creme 15%":                    "cream half and half",
    "creme sure":                   "cream sour",
    "fromage cheddar":              "cheese cheddar",
    "fromage mozzarella":           "cheese mozzarella",
    "fromage parmesan":             "cheese parmesan",
    "fromage feta":                 "cheese feta",
    "fromage ricotta":              "cheese ricotta",
    "fromage cottage":              "cheese cottage",
    "fromage cream":                "cheese cream",
    "fromage a la creme":           "cheese cream",
    "fromage de chevre":            "cheese goat",
    "fromage suisse":               "cheese swiss",
    "fromage bleu":                 "cheese blue",
    "fromage brie":                 "cheese brie",
    "fromage rape":                 "cheese cheddar shredded",
    "fromage":                      "cheese",
    "yogourt":                      "yogurt plain whole",
    "yaourt":                       "yogurt plain whole",
    "beurre":                       "butter",
    "margarine":                    "margarine",
    # produce
    "oignon":                       "onion raw",
    "oignon vert":                  "onion green raw",
    "echalote":                     "shallot raw",
    "ail":                          "garlic raw",
    "celeri":                       "celery raw",
    "carotte":                      "carrot raw",
    "carottes":                     "carrot raw",
    "tomate":                       "tomato red raw",
    "tomates":                      "tomato red raw",
    "tomate en des":                "tomato red raw",
    "champignon":                   "mushroom raw",
    "champignons":                  "mushroom raw",
    "poivron":                      "pepper sweet raw",
    "poivron rouge":                "pepper red sweet raw",
    "poivron vert":                 "pepper green sweet raw",
    "concombre":                    "cucumber raw",
    "laitue":                       "lettuce raw",
    "epinard":                      "spinach raw",
    "epinards":                     "spinach raw",
    "brocoli":                      "broccoli raw",
    "chou-fleur":                   "cauliflower raw",
    "chou":                         "cabbage raw",
    "courgette":                    "zucchini raw",
    "patate":                       "potato raw",
    "pomme de terre":               "potato raw",
    "patate douce":                 "sweet potato raw",
    "pois":                         "peas green",
    "pois verts":                   "peas green",
    "feve":                         "beans",
    "feves germees":                "bean sprouts",
    "haricot":                      "beans green raw",
    "haricots verts":               "beans green raw",
    "mais":                         "corn yellow",
    "ananas":                       "pineapple raw",
    "pomme":                        "apple raw",
    "pommes":                       "apple raw",
    "banane":                       "banana raw",
    "raisin":                       "grape raw",
    "raisin sec":                   "raisin",
    "raisins secs":                 "raisin",
    "fraise":                       "strawberry raw",
    "fraises":                      "strawberry raw",
    "framboise":                    "raspberry raw",
    "bleuet":                       "blueberry raw",
    "bleuets":                      "blueberry raw",
    "orange":                       "orange raw",
    "citron":                       "lemon raw",
    "lime":                         "lime raw",
    "persil":                       "parsley fresh",
    "basilic":                      "basil fresh",
    "thym":                         "thyme",
    "origan":                       "oregano",
    "ciboulette":                   "chives",
    "menthe":                       "mint",
    "coriandre":                    "cilantro fresh",
    # grains & starches
    "farine":                       "flour wheat all-purpose",
    "farine tout usage":            "flour wheat all-purpose",
    "farine de ble":                "flour wheat",
    "riz":                          "rice white raw",
    "riz blanc":                    "rice white raw",
    "riz brun":                     "rice brown raw",
    "riz cuit":                     "rice white cooked",
    "macaroni":                     "macaroni cooked",
    "spaghetti":                    "spaghetti cooked",
    "pates":                        "pasta cooked",
    "pain":                         "bread white",
    "biscotte":                     "toast melba",
    "chapelure":                    "bread crumbs dry",
    "avoine":                       "oats",
    "flocon d'avoine":              "oats",
    "flocons d'avoine":             "oats",
    "couscous":                     "couscous cooked",
    "quinoa":                       "quinoa cooked",
    "tortilla":                     "tortilla flour",
    # condiments / fats
    "huile":                        "oil vegetable",
    "huile d'olive":                "oil olive",
    "huile vegetale":               "oil vegetable",
    "huile de canola":              "oil canola",
    "vinaigre":                     "vinegar",
    "vinaigre de vin":              "vinegar red wine",
    "vinaigre balsamique":          "vinegar balsamic",
    "sauce soya":                   "sauce soy",
    "sauce soja":                   "sauce soy",
    "ketchup":                      "ketchup",
    "moutarde":                     "mustard yellow",
    "mayonnaise":                   "mayonnaise",
    "mayo":                         "mayonnaise",
    "miel":                         "honey",
    "sirop d'erable":               "syrup maple",
    "sirop":                        "syrup",
    "melasse":                      "molasses",
    "sel":                          "salt table",
    "poivre":                       "pepper black",
    "sel et poivre":                "salt table",
    "paprika":                      "paprika",
    "cumin":                        "cumin",
    "muscade":                      "nutmeg",
    "cannelle":                     "cinnamon",
    "vanille":                      "vanilla extract",
    # baking
    "sucre":                        "sugar granulated",
    "cassonade":                    "sugar brown",
    "poudre a pate":                "leavening agents baking powder",
    "soda a pate":                  "leavening agents baking soda",
    "bicarbonate":                  "leavening agents baking soda",
    "levure":                       "yeast bakers",
    "cacao":                        "cocoa unsweetened",
    "chocolat":                     "chocolate dark",
    "chocolat noir":                "chocolate dark",
    "chocolat au lait":             "chocolate milk",
    "brisures de chocolat":         "chocolate chips",
    # legumes / nuts
    "lentille":                     "lentils cooked",
    "pois chiche":                  "chickpeas canned",
    "pois chiches":                 "chickpeas canned",
    "haricot rouge":                "kidney beans canned",
    "haricot noir":                 "black beans canned",
    "noix":                         "walnuts",
    "amande":                       "almonds",
    "amandes":                      "almonds",
    "pacane":                       "pecans",
    "pecan":                        "pecans",
    "arachide":                     "peanuts",
    "beurre d'arachide":            "peanut butter",
    "tofu":                         "tofu",
    # bouillons / broths
    "bouillon de poulet":           "broth chicken",
    "bouillon de boeuf":            "broth beef",
    "bouillon de legumes":          "broth vegetable",
    # canned / packaged
    "soupe aux tomates":            "soup tomato canned condensed",
    "creme de champignon":          "soup mushroom canned condensed",
    "creme de poulet":              "soup chicken canned condensed",
    # additional herbs / spices / seasonings
    "laurier":                      "spices bay leaf",
    "feuille de laurier":           "spices bay leaf",
    "feuilles de laurier":          "spices bay leaf",
    "marjolaine":                   "spices marjoram",
    "sarriette":                    "spices savory",
    "romarin":                      "spices rosemary",
    "estragon":                     "spices tarragon",
    "cerfeuil":                     "spices chervil",
    "fenouil":                      "fennel raw",
    "anis":                         "spices anise",
    "gingembre":                    "spices ginger",
    "curcuma":                      "spices turmeric",
    "clou de girofle":              "spices cloves",
    "clou de girofle moulu":        "spices cloves",
    "clous de girofle":             "spices cloves",
    "poudre de chili":              "spices chili powder",
    "chili":                        "spices chili powder",
    "cayenne":                      "spices cayenne",
    "graine de moutarde":           "spices mustard seed",
    "moutarde seche":               "spices mustard ground",
    # condiments & sauces
    "sauce worcestershire":         "sauce worcestershire",
    "worcestershire":               "sauce worcestershire",
    "sauce hp":                     "sauce worcestershire",
    "sauce a steak":                "sauce worcestershire",
    "tabasco":                      "sauce hot tabasco",
    "salsa":                        "sauce salsa",
    "soya":                         "sauce soy",
    "soja":                         "sauce soy",
    "consomme":                     "broth beef",
    "bovril":                       "broth beef concentrate",
    "cube de bouillon":             "soup bouillon cube",
    "cubes de bouillon":            "soup bouillon cube",
    # alcohol used in cooking
    "vin":                          "wine table",
    "vin blanc":                    "wine white",
    "vin rouge":                    "wine red",
    "biere":                        "beer regular",
    "brandy":                       "alcohol brandy",
    "whisky":                       "alcohol whiskey",
    "rhum":                         "alcohol rum",
    "sherry":                       "wine sherry",
    "porto":                        "wine port",
    # baking — additions
    "fecule":                       "cornstarch",
    "fecule de mais":               "cornstarch",
    "corn starch":                  "cornstarch",
    "cornstarch":                   "cornstarch",
    "gelatine":                     "gelatin",
    "gelatine knox":                "gelatin",
    "graisse":                      "shortening vegetable",
    "saindoux":                     "lard",
    "shortening":                   "shortening vegetable",
    # cereals / breakfast
    "gruau":                        "oats",
    "rice krispies":                "cereal rice crisp",
    "corn flakes":                  "cereal corn flakes",
    "all bran":                     "cereal bran",
    # fruits / dried
    "datte":                        "dates",
    "dattes":                       "dates",
    "pruneau":                      "prunes",
    "pruneaux":                     "prunes",
    "abricot sec":                  "apricot dried",
    "canneberge":                   "cranberry",
    "canneberges":                  "cranberry",
    "cerise":                       "cherry raw",
    "cerises":                      "cherry raw",
    # vegetables — additions
    "navet":                        "turnip raw",
    "courge":                       "squash winter",
    "rutabaga":                     "rutabaga raw",
    "panais":                       "parsnip raw",
    "betterave":                    "beet raw",
    "asperge":                      "asparagus raw",
    "asperges":                     "asparagus raw",
    "piment":                       "pepper sweet raw",
    "piment vert":                  "pepper green sweet raw",
    "piment rouge":                 "pepper red sweet raw",
    # cheeses — additions
    "cheddar":                      "cheese cheddar",
    "cheddar blanc":                "cheese cheddar",
    "cheddar fort":                 "cheese cheddar sharp",
    "mozzarella":                   "cheese mozzarella",
    "parmesan":                     "cheese parmesan",
    "feta":                         "cheese feta",
    "ricotta":                      "cheese ricotta",
    "cottage":                      "cheese cottage",
    "philadelphia":                 "cheese cream",
    "gruyere":                      "cheese gruyere",
    "brie":                         "cheese brie",
    # misc
    "capres":                       "capers",
    "olive":                        "olives black",
    "olives":                       "olives black",
    "olives noires":                "olives black",
    "olives vertes":                "olives green",
    "cornichon":                    "pickle cucumber",
    "cornichons":                   "pickle cucumber",
    "marinade":                     "pickle cucumber",
    "salsa":                        "sauce salsa",
    "tortilla":                     "tortilla flour",
    "pate a croissant":             "dough croissant refrigerated",
    "pate a egg roll":              "wonton wrappers",
    "sauce bechamel":               "sauce white",
    "sauce brune":                  "gravy brown",
    "poudre a pate":                "leavening agents baking powder",
    "p a pate":                     "leavening agents baking powder",
    "p. a pate":                    "leavening agents baking powder",
    "soda a pate":                  "leavening agents baking soda",
    "s a pate":                     "leavening agents baking soda",
    "soda":                         "leavening agents baking soda",     # standalone abbrev common in this cookbook
    "levure":                       "yeast",
    "levure a pain":                "yeast",
    "levure seche":                 "yeast",
    "levure chimique":              "leavening agents baking powder",
    "bouillon":                     "broth chicken",     # default — most recipes mean chicken broth
    # seafood
    "moule":                        "mollusks mussel",
    "moules":                       "mollusks mussel",
    "calmar":                       "squid",
    "calmars":                      "squid",
    "homard":                       "lobster",
    "crabe":                        "crab",
    "huitre":                       "oysters",
    "huitres":                      "oysters",
    "anchois":                      "anchovy",
    "morue":                        "fish cod",
    "fletan":                       "fish halibut",
    "sole":                         "fish sole",
    "tilapia":                      "fish tilapia",
    "truite":                       "fish trout",
    "sardine":                      "fish sardine",
    "sardines":                     "fish sardine",
    # generic produce / mixes
    "legumes":                      "vegetables mixed",
    "legumes melanges":             "vegetables mixed",
    "legumes congeles":             "vegetables mixed frozen",
    "macedoine":                    "vegetables mixed",
    "fruits":                       "fruit mixed",
    "fruits congeles":              "fruit mixed frozen",
    "noix melangees":               "nuts mixed",
    "graines melangees":            "seeds mixed",
    "coeurs d'artichauts":          "artichoke hearts",
    "coeurs d'artichaut":           "artichoke hearts",
    "artichaut":                    "artichoke",
    "artichauts":                   "artichoke",
    "peche":                        "peach raw",
    "peches":                       "peach raw",
    "poire":                        "pear raw",
    "poires":                       "pear raw",
    "rhubarbe":                     "rhubarb",
    "tapioca":                      "tapioca pearl dry",
    "orge":                         "barley pearled",
    "couscous":                     "couscous cooked",
    "sauge":                        "spices sage",
    "graines d'aneth":              "spices dill seed",
    "aneth":                        "dill fresh",
    "graines de sesame":            "seeds sesame",
    "sesame":                       "seeds sesame",
    "graines de tournesol":         "seeds sunflower",
    "graines de lin":               "flax seeds",
    "graines de chia":              "chia seeds",
    "guimauve":                     "candies marshmallows",
    "guimauves":                    "candies marshmallows",
    "miracle whip":                 "salad dressing",
    "tabasco":                      "sauce hot tabasco",
    "salsa":                        "sauce salsa",
    "pesto":                        "sauce pesto",
    "prosciutto":                   "ham prosciutto",
    "curry":                        "spices curry powder",
    "cari":                         "spices curry powder",
    "cajun":                        "spices cajun",
    "the":                          "tea brewed",
    "the noir":                     "tea brewed",
    "the fort":                     "tea brewed",
    "cafe":                         "coffee brewed",
    "fruits de mer":                "seafood mixed",
    "palourdes":                    "clams",
    "filet de mahi":                "fish mahi-mahi",
    "carrelet":                     "fish flounder",
    "croute a tarte":               "pie crust",
    "biscuit":                      "biscuits cookies",
    "biscuits":                     "biscuits cookies",
    "biscuit ritz":                 "crackers ritz",
    "ritz":                         "crackers ritz",
    "noix de coco":                 "coconut shredded",
    "coco":                         "coconut shredded",
    "noix de cajou":                "cashews",
    "noix de grenoble":             "walnuts",
    "noisette":                     "hazelnuts",
    "pistache":                     "pistachios",
    "fruit confit":                 "fruit candied mixed",
    "fruits confits":               "fruit candied mixed",
    "epices":                       "spices",
    "epices a soupe":               "spices",
    "fines herbes":                 "spices italian seasoning",
    "soupe":                        "soup",
    "bechamel":                     "sauce white",
    "bechamelle":                   "sauce white",
    "demi-glace":                   "gravy brown",
    "glutamate":                    "salt monosodium glutamate",
    "msg":                          "salt monosodium glutamate",
    "gras":                         "shortening vegetable",
    "nectar":                       "juice",
    "mangue":                       "mango raw",
    "kiwi":                         "kiwi raw",
    # generic fallbacks
    "eau":                          "water",
}


# ============================================================================
# 3. INGREDIENT PARSER
# ============================================================================
UNICODE_FRACTIONS = {
    "½": 0.5, "⅓": 1/3, "⅔": 2/3, "¼": 0.25, "¾": 0.75,
    "⅕": 0.2, "⅖": 0.4, "⅗": 0.6, "⅘": 0.8,
    "⅙": 1/6, "⅚": 5/6, "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875,
}

# Unit synonyms → canonical key (matches ML_PER_UNIT, GRAMS_PER_UNIT, COUNT_DEFAULTS).
UNIT_SYNONYMS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^kg$|^kilo(?:gramme)?s?$", re.I),                      "kg"),
    (re.compile(r"^g$|^gr$|^gramme?s?$", re.I),                          "g"),
    (re.compile(r"^lb$|^lbs$|^livres?$|^pounds?$", re.I),                "lb"),
    (re.compile(r"^oz$|^onces?$|^ounces?$", re.I),                       "oz"),
    (re.compile(r"^l$|^litre?s?$", re.I),                                "l"),
    (re.compile(r"^ml$|^millilitre?s?$", re.I),                          "ml"),
    (re.compile(r"^t$|^tasse?s?$|^cup?s?$", re.I),                       "tasse"),
    (re.compile(
        r"^(?:c\.?|cuill[eè]res?)\s*[aà]?\s*(?:soupe|tab(?:le)?)$|^cas$|^tbsp$|^tbs$|^cs$",
        re.I), "c_soupe"),
    (re.compile(
        r"^(?:c\.?|cuill[eè]res?)\s*[aà]?\s*(?:th[eé]|tea)$|^cac$|^tsp$|^cc$|^ct$",
        re.I), "c_the"),
    (re.compile(r"^pinc[eé]es?$", re.I),                                 "pincee"),
    (re.compile(r"^oeufs?$|^œufs?$|^eggs?$", re.I),                      "oeuf"),
    (re.compile(r"^gousses?$", re.I),                                    "gousse"),
    (re.compile(r"^branches?$", re.I),                                   "branche"),
    (re.compile(r"^tranche?s?$", re.I),                                  "tranche"),
    (re.compile(r"^paquets?$", re.I),                                    "paquet"),
    (re.compile(r"^bo[iî]tes?$", re.I),                                  "boite"),
    (re.compile(r"^sachets?$", re.I),                                    "sachet"),
    (re.compile(r"^feuilles?$", re.I),                                   "feuille"),
]


def normalize(s: str) -> str:
    """Lowercase + strip accents + collapse whitespace, keep apostrophes/punct light."""
    if s is None:
        return ""
    # Pre-fold ligatures NFKD does not split (œ → oe, æ → ae)
    s = s.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = s.replace("’", "'").replace("`", "'").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_quantity(s: str) -> tuple[Optional[float], str]:
    """Pull a leading quantity (number, fraction, mixed, unicode-fraction) off.
    Returns (qty_float_or_None, remainder_string).

    Range handling: '4 a 4 1/2 tasses ...' or '3 a 4 gousses' takes the midpoint.
    """
    s = s.strip()
    # Range: NUM (a|to|-) NUM. Capture both sides, take midpoint, then continue parse on tail.
    range_pat = re.compile(
        r"^(\d+(?:[/\.,]\d+)?(?:\s+\d+/\d+)?)\s*(?:a|to|-)\s+(\d+(?:[/\.,]\d+)?(?:\s+\d+/\d+)?)\b",
        re.I)
    m = range_pat.match(s)
    if m:
        def to_float(token: str) -> float:
            token = token.strip()
            if " " in token and "/" in token:
                whole, frac = token.split(maxsplit=1)
                num, den = frac.split("/")
                return int(whole) + int(num) / int(den)
            if "/" in token:
                num, den = token.split("/")
                return int(num) / int(den)
            return float(token.replace(",", "."))
        try:
            lo, hi = to_float(m.group(1)), to_float(m.group(2))
            mid = (lo + hi) / 2
            return mid, s[m.end():].strip()
        except (ValueError, ZeroDivisionError):
            pass
    # leading unicode fraction
    if s and s[0] in UNICODE_FRACTIONS:
        return UNICODE_FRACTIONS[s[0]], s[1:].strip()
    # mixed number "1 1/2" or "1 ½"
    m = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)\b", s)
    if m:
        whole, num, den = (int(x) for x in m.groups())
        return whole + num / den, s[m.end():].strip()
    m = re.match(r"^(\d+)\s+([½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])", s)
    if m:
        return int(m.group(1)) + UNICODE_FRACTIONS[m.group(2)], s[m.end():].strip()
    # plain fraction "1/2"
    m = re.match(r"^(\d+)\s*/\s*(\d+)\b", s)
    if m:
        return int(m.group(1)) / int(m.group(2)), s[m.end():].strip()
    # decimal (French comma OR dot)
    m = re.match(r"^(\d+(?:[.,]\d+)?)", s)
    if m:
        return float(m.group(1).replace(",", ".")), s[m.end():].strip()
    # spelled out
    if re.match(r"^(une?|un)\b", s, flags=re.I):
        return 1.0, re.sub(r"^(une?|un)\b", "", s, flags=re.I).strip()
    if re.match(r"^demi\b", s, flags=re.I):
        return 0.5, re.sub(r"^demi[ -]?", "", s, flags=re.I).strip()
    return None, s


def parse_unit(s: str) -> tuple[Optional[str], str]:
    """Pull a unit token off the front. Returns (unit_canonical_or_None, remainder)."""
    s = s.strip()
    # multi-word unit attempts (1- or 2- or 3-token) longest first
    tokens = s.split()
    for n in (3, 2, 1):
        if len(tokens) < n:
            continue
        head = " ".join(tokens[:n])
        # strip trailing punctuation from head for matching
        head_clean = head.rstrip(".,")
        for pat, canon in UNIT_SYNONYMS:
            if pat.match(head_clean):
                return canon, " ".join(tokens[n:]).strip()
    return None, s


def strip_filler(s: str) -> str:
    """Remove leading 'de '/'d''/'du '/'des '/'à '."""
    return re.sub(r"^(de\s+|d'|du\s+|des\s+|a\s+|au\s+|aux\s+)+", "", s, flags=re.I).strip()


@dataclass
class ParsedIngredient:
    raw: str
    qty: Optional[float]
    unit: Optional[str]              # canonical unit key, or None
    food_phrase: str                 # what's left after qty+unit stripped
    food_phrase_norm: str            # normalized
    notes: list[str] = field(default_factory=list)


# Quantity-format rescuers — convert ingredient lines whose qty isn't at the
# front into the canonical "<qty> <unit> <food>" shape so the regular parser
# can chew on them. Three formats observed in the cookbook:
#
#   1. Parenthetical:    "huile (1/4 tasse)"      -> "1/4 tasse huile"
#   2. Dash-separator:   "farine - 2 c à table"   -> "2 c à table farine"
#   3. Bare unit lead:   "pincée de sel"          -> "1 pincée de sel"
#
# These rescuers run on the NORMALIZED form (lowercased, accents stripped) and
# only fire when the trailing/parenthetical segment looks like a quantity.

_QTY_TOKEN = (
    r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?|"
    r"[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|une?|demi)"
)
_QTY_AT_END_PAREN = re.compile(r"^(.+?)\s*\((" + _QTY_TOKEN + r"[^)]*)\)\s*$", re.I)
_QTY_AT_END_DASH  = re.compile(r"^(.+?)\s*[-–]\s*(" + _QTY_TOKEN + r"\b.*)$", re.I)
_BARE_UNIT_LEAD   = re.compile(
    r"^(pince[eé]e?s?|gousses?|tranches?|paquets?|bo[iî]tes?|sachets?|"
    r"feuilles?|enveloppes?)\b",
    re.I,
)


def rescue_quantity_format(s: str) -> str:
    """Rewrite a normalized ingredient line so qty appears at the front.

    Returns the input unchanged if no rescue applies.
    """
    if not s:
        return s
    m = _QTY_AT_END_PAREN.match(s)
    if m:
        return f"{m.group(2).strip()} {m.group(1).strip()}"
    m = _QTY_AT_END_DASH.match(s)
    if m:
        # Avoid swallowing inline ranges like "4 a 4 1/2 tasses ..." that
        # already have qty at the front. The match only fires when the LEFT
        # side is non-numeric (a food phrase) and the RIGHT side starts with
        # a number — _QTY_TOKEN already enforces the latter.
        if re.match(r"^\s*[\d½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]", s):
            return s
        return f"{m.group(2).strip()} {m.group(1).strip()}"
    if _BARE_UNIT_LEAD.match(s):
        return "1 " + s
    return s


def parse_ingredient(raw: str) -> ParsedIngredient:
    s_norm = rescue_quantity_format(normalize(raw))
    qty, rest = parse_quantity(s_norm)
    rest = strip_filler(rest)
    unit, rest = parse_unit(rest)
    rest = strip_filler(rest)
    # Strip trailing modifiers that don't affect the food (parenthetical, "au goût", "haché", "frais").
    # IMPORTANT: many of these terms are *cooking adjectives*, not nouns — never strip mid-word.
    # The patterns below all use \b boundaries and listed forms only (not stems).
    rest = re.sub(r"\([^)]*\)", "", rest)             # parentheticals
    rest = re.sub(r"\bau gout\b.*$", "", rest)
    rest = re.sub(r"\b(hache|hachee|haches|hachees|rape|rapee|rapes|rapees|"
                  r"tranche|tranchee|tranches|tranchees|"
                  r"frais|fraiche|fraiches|"
                  r"en des|en lanieres?|en morceaux|en rondelles|en cubes?|en tranches?|"
                  r"cuit|cuite|cuits|cuites|cru|crue|crus|crues|"
                  r"refroidi|refroidie|au refrigerateur|au frigo|"
                  r"fondu|fondue|fondus|fondues|"
                  r"battu|battue|battus|battues|"
                  r"emiette|emiettee|emiettes|emiettees|"
                  r"fin|fine|fins|fines|petit|petite|petits|petites|"
                  r"gros|grosse|grosses|moyen|moyenne)\b", "", rest)
    rest = re.sub(r"\s*,\s*$", "", rest)
    rest = re.sub(r"\s+", " ", rest).strip()
    notes = []
    if qty is None:
        notes.append("no_quantity")
    if unit is None and qty is not None:
        notes.append("count_unit")  # bare "1 oeuf" — unit is implied by phrase
    return ParsedIngredient(raw=raw, qty=qty, unit=unit, food_phrase=rest,
                            food_phrase_norm=normalize(rest), notes=notes)


# ============================================================================
# 4. FOOD MATCHER (FR phrase → food_id)
# ============================================================================
class FoodMatcher:
    """Translate a French food phrase to a USDA-ish English query, then FTS5-match
    against the slim shipping DB; if no decent hit, fall back to canonical."""

    def __init__(self, slim_path: Path, canonical_path: Path):
        self.slim = sqlite3.connect(f"file:{slim_path.as_posix()}?mode=ro", uri=True)
        self.slim.row_factory = sqlite3.Row
        self.canon = sqlite3.connect(f"file:{canonical_path.as_posix()}?mode=ro", uri=True)
        self.canon.row_factory = sqlite3.Row
        # presort translation keys by length desc so "fromage cheddar" beats "fromage"
        self.trans_keys = sorted(TRANSLATION.keys(), key=len, reverse=True)
        self._cache: dict[str, tuple[Optional[str], float, str]] = {}

    def translate(self, phrase_norm: str) -> Optional[str]:
        if not phrase_norm:
            return None
        # Direct hit
        if phrase_norm in TRANSLATION:
            return TRANSLATION[phrase_norm]
        # Substring match (longest key first)
        for k in self.trans_keys:
            if k in phrase_norm:
                return TRANSLATION[k]
        return None

    def _fts_lookup(self, conn: sqlite3.Connection, query: str) -> Optional[tuple[str, str, float]]:
        """Run an FTS5 MATCH; return (food_id, display_name, score)."""
        if not query.strip():
            return None
        # Sanitize for FTS5: drop quotes, split into tokens, OR-join
        toks = re.findall(r"[a-z0-9]+", query.lower())
        if not toks:
            return None
        # Build a phrase with all tokens required (AND), tolerating prefix on last token.
        match_expr = " ".join(toks[:-1] + [toks[-1] + "*"]) if len(toks) > 1 else toks[0] + "*"
        try:
            row = conn.execute(
                "SELECT f.food_id, f.display_name, bm25(foods_fts) AS score "
                "FROM foods_fts JOIN foods f ON foods_fts.rowid = f.rowid "
                "WHERE foods_fts MATCH ? "
                "ORDER BY score LIMIT 1",
                (match_expr,)
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None:
            return None
        return row["food_id"], row["display_name"], row["score"]

    def _canonical_lookup(self, query: str) -> Optional[tuple[str, str, float]]:
        """LIKE-based search on canonical foods table; coarse but works as fallback."""
        toks = re.findall(r"[a-z0-9]+", query.lower())
        if not toks:
            return None
        # Order rows by how many tokens appear in name; prefer foundation/sr_legacy sources
        like_terms = " AND ".join(["LOWER(f.name) LIKE ?"] * len(toks))
        params = [f"%{t}%" for t in toks]
        sql = (
            "SELECT f.food_id, f.display_name "
            "FROM foods f "
            f"WHERE {like_terms} "
            "ORDER BY LENGTH(f.name) ASC LIMIT 1"
        )
        try:
            row = self.canon.execute(sql, params).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None:
            return None
        # Synthetic score (lower is better in BM25 convention; use negative match length)
        return row["food_id"], row["display_name"], -float(len(toks))

    def match(self, phrase_norm: str, fallback_unit: Optional[str] = None
              ) -> tuple[Optional[str], float, str]:
        """Return (food_id_or_None, confidence_0_1, source_label).
        If phrase_norm is empty/unmatched and fallback_unit names a food
        (e.g., 'oeuf'), retry using the unit as the search key."""
        cache_key = (phrase_norm, fallback_unit)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        eng = self.translate(phrase_norm) if phrase_norm else None
        if not eng and fallback_unit:
            eng = self.translate(fallback_unit)
        result: tuple[Optional[str], float, str] = (None, 0.0, "no_translation")
        if eng:
            slim_hit = self._fts_lookup(self.slim, eng)
            if slim_hit:
                fid, _name, score = slim_hit
                conf = 0.85 if score < -2 else (0.70 if score < 0 else 0.55)
                if not phrase_norm and fallback_unit:
                    conf *= 0.9      # slight haircut: relied on unit alone
                result = (fid, conf, "slim_fts" if phrase_norm else "slim_fts_unit")
            else:
                canon_hit = self._canonical_lookup(eng)
                if canon_hit:
                    fid, _name, _score = canon_hit
                    result = (fid, 0.55, "canonical_like")
        self._cache[cache_key] = result
        return result


# ============================================================================
# 5. UNIT → GRAMS
# ============================================================================
def density_for(phrase_norm: str) -> tuple[float, str]:
    """Pick a density (g/ml) for a given normalized food phrase."""
    if not phrase_norm:
        return DEFAULT_DENSITY, "default"
    for kw, dens in DENSITY_BY_KEYWORD:
        if kw in phrase_norm:
            return dens, kw
    return DEFAULT_DENSITY, "default"


def _kw_in_phrase(kw: str, phrase_norm: str) -> bool:
    """Word-boundary match — avoids 'oeuf' matching inside 'boeuf'."""
    if not phrase_norm:
        return False
    return re.search(rf"\b{re.escape(kw)}\b", phrase_norm) is not None


def count_grams_for(unit: str, phrase_norm: str) -> tuple[float, str]:
    """Return grams-per-item for count units, with food-specific overrides."""
    for kw, table in COUNT_OVERRIDES:
        if _kw_in_phrase(kw, phrase_norm):
            if unit in table:
                return table[unit], f"override:{kw}"
            if "unit" in table and unit not in COUNT_DEFAULTS:
                return table["unit"], f"override:{kw}"
    return COUNT_DEFAULTS.get(unit, 30.0), "default_count"


def convert_to_grams(p: ParsedIngredient) -> tuple[Optional[float], float, str]:
    """Return (grams, confidence_0_1, method_label). None grams if unconvertible."""
    if p.qty is None:
        return None, 0.0, "no_qty"
    u = p.unit
    # Bare-number with implied count item ("1 oeuf", "2 oignons", "1 brocoli")
    if u is None:
        if any(_kw_in_phrase(kw, p.food_phrase_norm) for kw, _ in COUNT_OVERRIDES):
            g, label = count_grams_for("unit", p.food_phrase_norm)
            return p.qty * g, 0.65, f"count_implied:{label}"
        return None, 0.0, "no_unit_no_count_match"
    # Weight units — exact
    if u in GRAMS_PER_UNIT:
        return p.qty * GRAMS_PER_UNIT[u], 0.95, f"weight:{u}"
    # Volume units — need density
    if u in ML_PER_UNIT:
        ml = p.qty * ML_PER_UNIT[u]
        dens, dens_src = density_for(p.food_phrase_norm)
        conf = 0.80 if dens_src != "default" else 0.45
        return ml * dens, conf, f"volume:{u}->ml*dens({dens_src}={dens})"
    # Count units
    if u in COUNT_DEFAULTS:
        g, label = count_grams_for(u, p.food_phrase_norm)
        # paquet/boite are very vague
        conf = 0.40 if u in ("paquet", "boite", "sachet") else 0.65
        return p.qty * g, conf, f"count:{u}({label})"
    return None, 0.0, f"unknown_unit:{u}"


# ============================================================================
# 6. NUTRIENT LOOKUP
# ============================================================================
def fetch_nutrients(conn: sqlite3.Connection, food_id: str) -> dict[str, tuple[float, str, str]]:
    """Return {nutrient_id: (value_per_100g, unit, display_name)}.
    Uses the slim DB schema first (food_nutrients table); for canonical food_ids
    that aren't in the slim DB we fall back to the canonical view.
    """
    rows = conn.execute(
        "SELECT n.nutrient_id, n.display_name, n.canonical_unit, fn.value_per_100g "
        "FROM food_nutrients fn JOIN nutrients n ON fn.nutrient_id = n.nutrient_id "
        "WHERE fn.food_id = ?",
        (food_id,)
    ).fetchall()
    return {r["nutrient_id"]: (r["value_per_100g"], r["canonical_unit"], r["display_name"])
            for r in rows}


def fetch_nutrients_canonical(conn: sqlite3.Connection, food_id: str,
                              nutrient_ids: list[str]) -> dict[str, tuple[float, str, str]]:
    """Canonical DB fallback: use v_consensus_nutrients view × nutrients table.
    Only fetch the BOS-core 40 (passed in as nutrient_ids)."""
    if not nutrient_ids:
        return {}
    placeholders = ",".join("?" * len(nutrient_ids))
    rows = conn.execute(
        f"SELECT v.nutrient_id, n.display_name, n.canonical_unit, v.value_per_100g "
        f"FROM v_consensus_nutrients v JOIN nutrients n ON v.nutrient_id = n.nutrient_id "
        f"WHERE v.food_id = ? AND v.nutrient_id IN ({placeholders})",
        [food_id, *nutrient_ids]
    ).fetchall()
    return {r["nutrient_id"]: (r["value_per_100g"], r["canonical_unit"], r["display_name"])
            for r in rows}


# ============================================================================
# 7. AGGREGATOR + DRIVER
# ============================================================================
def is_quantified(s: str) -> bool:
    """An ingredient is "quantified" if any rescuer can put a qty at the front.

    This must stay aligned with parse_ingredient — anything is_quantified
    accepts must be parseable by the main pipeline.
    """
    if not isinstance(s, str): return False
    s = s.strip()
    if not s: return False
    s_rescued = rescue_quantity_format(normalize(s))
    if re.match(r"^\s*(?:\d+\s*[/\.,]?\s*\d*|[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])", s_rescued): return True
    if re.match(r"^\s*(une?|un|demi[ -]?|quelques)\b", s_rescued, flags=re.I): return True
    return False


def aggregate_recipe(recipe: dict, matcher: FoodMatcher,
                     bos_core_nutrients: list[str]) -> dict:
    """Process one recipe end-to-end. Returns a serializable result dict."""
    title = recipe.get("title", "")
    rid   = recipe.get("id")
    label = recipe.get("numberLabel")
    raw_servings = (recipe.get("meta") or {}).get("servings")
    servings = raw_servings if (isinstance(raw_servings, (int, float)) and raw_servings > 0) else None
    servings_imputed = servings is None
    # For computation we need a divisor, but we'll mark per_serving as None when imputed.
    divisor = servings if servings else 1

    totals: dict[str, float] = {n: 0.0 for n in bos_core_nutrients}
    units: dict[str, str] = {}
    total_grams = 0.0
    low_conf_grams = 0.0
    per_ingredient = []

    skipped_unquantified = 0
    for raw in recipe.get("ingredients", []) or []:
        if not isinstance(raw, str): continue
        if not is_quantified(raw):
            # Phase 2+: unquantified line — skip but record. Treats it as 0g
            # contribution, biasing the recipe slightly low for seasonings.
            skipped_unquantified += 1
            per_ingredient.append({
                "raw": raw, "qty": None, "unit": None, "food_phrase": "",
                "food_id": None, "match_source": "skipped_no_qty",
                "match_conf": 0.0, "grams": None, "conv_method": "skipped_no_qty",
                "conv_conf": 0.0, "combined_conf": 0.0, "notes": ["skipped_no_qty"],
            })
            continue
        p = parse_ingredient(raw)
        food_id, match_conf, match_src = matcher.match(
            p.food_phrase_norm, fallback_unit=p.unit)
        grams, conv_conf, conv_method = convert_to_grams(p)

        nutrient_lines: dict[str, float] = {}
        if food_id and grams is not None:
            nutrients = fetch_nutrients(matcher.slim, food_id)
            if not nutrients:
                nutrients = fetch_nutrients_canonical(matcher.canon, food_id, bos_core_nutrients)
            for nid, (val100, unit, _name) in nutrients.items():
                if nid in totals:
                    contrib = (grams / 100.0) * val100
                    totals[nid] += contrib
                    nutrient_lines[nid] = contrib
                    units[nid] = unit
            total_grams += grams
            combined_conf = match_conf * conv_conf
            if combined_conf < 0.40:
                low_conf_grams += grams
        else:
            combined_conf = 0.0

        per_ingredient.append({
            "raw":           raw,
            "qty":           p.qty,
            "unit":          p.unit,
            "food_phrase":   p.food_phrase,
            "food_id":       food_id,
            "match_source":  match_src,
            "match_conf":    round(match_conf, 2),
            "grams":         round(grams, 2) if grams is not None else None,
            "conv_method":   conv_method,
            "conv_conf":     round(conv_conf, 2),
            "combined_conf": round(combined_conf, 2),
            "notes":         p.notes,
        })

    per_serving = ({n: round(v / divisor, 3) for n, v in totals.items()}
                   if not servings_imputed else None)
    per_100g = ({n: round(v / total_grams * 100.0, 3) for n, v in totals.items()}
                if total_grams > 0 else None)

    low_conf_ratio = (low_conf_grams / total_grams) if total_grams > 0 else 1.0

    return {
        "id":             rid,
        "title":          title,
        "numberLabel":    label,
        "servings":       servings,
        "servings_imputed": servings_imputed,
        "skipped_unquantified": skipped_unquantified,
        "ingredient_count": len(per_ingredient),
        "matched_count":  sum(1 for x in per_ingredient if x["food_id"]),
        "total_grams":    round(total_grams, 1),
        "low_conf_ratio": round(low_conf_ratio, 3),
        "totals":         {n: round(v, 3) for n, v in totals.items()},
        "per_serving":    per_serving,
        "per_100g":       per_100g,
        "units":          units,
        "ingredients":    per_ingredient,
    }


def main() -> int:
    # Force UTF-8 on stdout so log lines with French / arrows don't crash on Windows cp1252.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Optional CLI: --min-quantified <0..1>  (default 1.0 = phase 1 behavior)
    min_q = 1.0
    out_suffix = ""
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--min-quantified" and i + 1 < len(args):
            min_q = float(args[i + 1]); i += 2
        elif args[i] == "--out-suffix" and i + 1 < len(args):
            out_suffix = args[i + 1]; i += 2
        else:
            i += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []
    def log(msg: str):
        print(msg)
        log_lines.append(msg)

    log(f"Loading recipes from {RECIPES_JSON}")
    with open(RECIPES_JSON, encoding="utf-8") as f:
        recipes = json.load(f)
    log(f"Total recipes: {len(recipes)}")
    log(f"min_quantified threshold: {min_q:.0%}  (recipes with >= this share of quantified lines are eligible)")

    eligible = []
    for r in recipes:
        ings = r.get("ingredients") or []
        if not ings: continue
        q = sum(1 for i in ings if is_quantified(i))
        if q / len(ings) >= min_q:
            eligible.append(r)
    log(f"Eligible recipes: {len(eligible)}")
    fully_q = eligible

    matcher = FoodMatcher(SLIM_DB, CANONICAL_DB)

    bos_core_nutrients = [r[0] for r in matcher.slim.execute(
        "SELECT nutrient_id FROM nutrients ORDER BY nutrient_id").fetchall()]
    log(f"BOS-core nutrients: {len(bos_core_nutrients)} → {bos_core_nutrients[:6]}…")

    results = []
    unmatched = Counter()              # only real unmatched (not skipped_no_qty)
    for i, r in enumerate(fully_q, 1):
        try:
            res = aggregate_recipe(r, matcher, bos_core_nutrients)
            results.append(res)
            for ing in res["ingredients"]:
                if ing["match_source"] == "skipped_no_qty":
                    continue          # not an unmatched failure — it was skipped on purpose
                if not ing["food_id"]:
                    key = normalize(ing["food_phrase"]) or ing["raw"]
                    unmatched[key] += 1
            if i % 25 == 0:
                log(f"  processed {i}/{len(fully_q)}")
        except Exception as e:
            log(f"  ERROR on {r.get('numberLabel')} {r.get('title')[:40]}: {e}")

    out_main = OUT_DIR / f"recipes_nutrition{out_suffix or '_phase1'}.json"
    with open(out_main, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": 1,
            "generated_from": str(RECIPES_JSON),
            "recipe_count":   len(results),
            "nutrient_ids":   bos_core_nutrients,
            "recipes":        results,
        }, f, ensure_ascii=False, indent=2)
    log(f"Wrote {out_main}")

    out_unmatched = OUT_DIR / f"unmatched_phrases{out_suffix}.csv"
    with open(out_unmatched, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["count", "phrase"])
        for phrase, count in unmatched.most_common():
            w.writerow([count, phrase])
    log(f"Wrote {out_unmatched} ({len(unmatched)} distinct unmatched phrases)")

    out_low = OUT_DIR / f"low_confidence_recipes{out_suffix}.csv"
    with open(out_low, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["numberLabel", "title", "match_ratio", "low_conf_ratio",
                    "total_grams", "ingredient_count"])
        for r in results:
            match_ratio = (r["matched_count"] / r["ingredient_count"]
                           if r["ingredient_count"] else 0.0)
            if match_ratio < 0.80 or r["low_conf_ratio"] > 0.30:
                w.writerow([r["numberLabel"], r["title"], round(match_ratio, 2),
                            r["low_conf_ratio"], r["total_grams"], r["ingredient_count"]])
    log(f"Wrote {out_low}")

    # Summary stats — distinguish quantified from total ingredients.
    total_ing  = sum(r['ingredient_count']        for r in results)
    skipped    = sum(r['skipped_unquantified']   for r in results)
    quantified = total_ing - skipped
    matched    = sum(r['matched_count']           for r in results)
    # Match rate against quantified ingredients only (the real signal).
    matched_pcts = []
    for r in results:
        denom = r['ingredient_count'] - r['skipped_unquantified']
        if denom > 0:
            matched_pcts.append(r['matched_count'] / denom)
    low_conf_pcts = [r["low_conf_ratio"] for r in results]
    log("")
    log("=== SUMMARY ===")
    log(f"  recipes processed              : {len(results)}")
    log(f"  total ingredient lines         : {total_ing}")
    log(f"    of which quantified          : {quantified}")
    log(f"    of which skipped (no qty)    : {skipped}")
    log(f"  matched (quantified) ingredients: {matched}")
    if matched_pcts:
        log(f"  mean match rate (over quantified): {sum(matched_pcts)/len(matched_pcts):.1%}")
    if low_conf_pcts:
        log(f"  median low-conf mass            : {sorted(low_conf_pcts)[len(low_conf_pcts)//2]:.1%}")
    log(f"  unmatched phrases (real fails) : {len(unmatched)}  (top → {[p for p,_ in unmatched.most_common(8)]})")

    with open(OUT_DIR / "phase1_run.log", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
