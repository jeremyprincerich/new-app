"""Merge BOOK1 transcribed soup recipes into recipes.json + categories.json.

Idempotent: if recipes with the same source filename already exist (matched via
notes containing "BOOK1/<filename>.heic"), they are skipped.

Run from new-app/: `python tools/merge_book1_recipes.py`
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes.json"
CATS_PATH = ROOT / "categories.json"

VERIFY_NOTE = (
    "Transcrit automatiquement depuis BOOK1/{src} — "
    "à vérifier (titre, quantités et étapes peuvent contenir des erreurs)."
)


# Each entry: source HEIC filename, title, ingredients[], steps[].
# Transcribed from cursive handwritten French — quantities and word-level
# guesses flagged with the standard verification note.
NEW_RECIPES = [
    # --- page 1 (101055) ---
    {
        "src": "20260503_101055.heic",
        "title": "Crème de tomate maison de Sœur Angèle",
        "ingredients": [
            "6 grosses tomates",
            "1 oignon",
            "huile d'olive",
            "1 pomme de terre en tranches très minces",
            "1 cube ou 3/4 tasse de bouillon de poulet",
            "1 c. à soupe de basilic frais (ou 1/2 c. à thé déshydraté)",
            "1 c. à thé de pâte de tomate",
            "sel, poivre",
            "crème (au goût)",
        ],
        "steps": [
            "Chauffer l'huile, faire revenir l'oignon.",
            "Ajouter les tomates, cuire 5 à 6 min.",
            "Ajouter les pommes de terre, le bouillon, le basilic et la pâte de tomate.",
            "Mijoter environ 20 min, mixer (Mélangeur Kenta).",
            "Ajouter la crème un peu avant de servir, saler et poivrer.",
        ],
    },
    {
        "src": "20260503_101055.heic",
        "title": "Chaudrée de palourdes",
        "ingredients": [
            "2 c. à soupe de beurre",
            "1 branche de céleri en dés",
            "2 c. à soupe de farine",
            "3 tasses de bouillon de poulet (ou jus de palourdes)",
            "3 tasses de pommes de terre en dés",
            "1 boîte de palourdes",
            "1 tasse de crème (5% ou 35%)",
            "sel, poivre",
        ],
        "steps": [
            "Fondre le beurre, faire revenir l'oignon et le céleri 5 min.",
            "Ajouter la farine, mélanger.",
            "Ajouter le bouillon, les pommes de terre et les palourdes.",
            "Mijoter dans une casserole environ 20 min.",
            "Lorsque la soupe est prête, ajouter la crème (en réservant quelques palourdes), saler et poivrer.",
        ],
        "notes_extra": "Si la soupe est trop épaisse, ajouter un peu de bouillon avant de servir.",
    },
    # --- page 2 (101123) ---
    {
        "src": "20260503_101123.heic",
        "title": "Crème de poireaux",
        "ingredients": [
            "3 oignons",
            "1 pomme de terre",
            "2 1/2 tasses de bouillon de poulet",
            "1/2 c. à thé de basilic",
            "1/2 c. à thé de thym",
            "1 c. à soupe de beurre",
            "crème ou lait au goût",
            "sel, poivre",
        ],
        "steps": [
            "Faire revenir les oignons dans le beurre.",
            "Ajouter la pomme de terre en dés, le bouillon, le basilic et le thym.",
            "Couvrir, mijoter à feu doux environ 30 min, jusqu'à ce que la pomme de terre soit cuite.",
            "Passer au mélangeur (blender).",
            "Ajouter la crème ou le lait au goût.",
        ],
    },
    {
        "src": "20260503_101123.heic",
        "title": "Soupe de poire et poivron",
        "ingredients": [
            "2 poires",
            "1 poivron",
            "1 c. à soupe d'huile d'olive",
            "1 oignon",
            "1 cube de bouillon de légumes",
            "1 tasse d'eau",
            "2 c. à soupe de lait",
            "sel, poivre",
        ],
        "steps": [
            "Faire revenir l'oignon en dés dans l'huile environ 4 min.",
            "Ajouter le poivron en dés, cuire 2 min.",
            "Ajouter les poires en dés, le bouillon et l'eau, mijoter 20 à 30 min.",
            "Mélanger au blender, ajouter le lait, saler et poivrer.",
        ],
    },
    # --- page 3 (101137) ---
    {
        "src": "20260503_101137.heic",
        "title": "Crème de chou-fleur au cheddar",
        "ingredients": [
            "1 chou-fleur",
            "1 oignon",
            "1 gousse d'ail",
            "1 c. à soupe de farine",
            "1 1/2 tasse de cheddar fort râpé",
            "1 patate",
            "bouillon de poulet",
            "sel, poivre",
            "persil",
        ],
        "steps": [
            "Faire revenir l'oignon et l'ail dans le beurre.",
            "Ajouter la patate et le chou-fleur en morceaux, le bouillon.",
            "Cuire 15 min jusqu'à tendre.",
            "Ajouter le cheddar et la farine délayée, brasser pour éviter les grumeaux.",
            "Mixer si désiré, saler et poivrer.",
        ],
    },
    {
        "src": "20260503_101137.heic",
        "title": "Crème de carotte-navet sans crème",
        "ingredients": [
            "1 oignon haché",
            "1 c. à soupe de beurre",
            "3 carottes",
            "4 navets en rondelles (ou 1 navet en morceaux)",
            "4 tasses de bouillon de poulet",
            "1/2 c. à thé de moutarde",
            "1/4 c. à thé de cardamome",
            "3 c. à soupe de sirop d'érable",
            "1/2 tasse de crème",
            "sel, poivre",
        ],
        "steps": [
            "Faire revenir l'oignon dans le beurre.",
            "Ajouter les carottes et navets, mouiller avec le bouillon.",
            "Mijoter 30 min ou jusqu'à tendre.",
            "Ajouter la moutarde, la cardamome, le sirop d'érable, sel et poivre.",
            "Passer au mélangeur (blender).",
        ],
    },
    # --- page 4 (101151) ---
    {
        "src": "20260503_101151.heic",
        "title": "Soupe tomate d'antan",
        "ingredients": [
            "huile d'olive",
            "1 gros oignon haché",
            "3/4 nouilles (alphabet ou autres)",
            "1 boîte de Vermicelli (ou autre pâte)",
            "1 boîte de tomates au four",
            "concassé de jambon au goût",
            "1 grosse carotte, 1 oignon",
            "5 min de feu vif, ajouter sucre",
            "bouillon de poulet, basilic",
            "sel, poivre",
        ],
        "steps": [
            "Faire revenir l'oignon dans l'huile.",
            "Ajouter les tomates, les légumes, le bouillon et le basilic.",
            "Cuire à feu mijoté environ 1 h 30 à 2 h.",
            "Ajouter les nouilles vers la fin.",
        ],
    },
    {
        "src": "20260503_101151.heic",
        "title": "Soupe poulet et nouilles facile (Salomon, 6 à 10 pers.)",
        "ingredients": [
            "1 tasse de macaroni mince",
            "2 c. à soupe de poulet en lanière",
            "1 branche de céleri en dés, 2 c. à soupe de farine",
            "3 g. d'ail, sel, poivre, 1/2 t. de bouillon de poulet en cubes (ou 1 1/2 t.)",
            "1 boulette de poulet cuit effilochée",
            "persil, chauffer crème au lait",
            "céleri, ail, oignon",
            "5 min, ou légumes attendris",
            "bouillon, légumes, poulet",
            "cuire, ajouter macaroni, mijoter 8 à 10 min",
            "ajouter de l'eau à la fin de cuisson",
        ],
        "steps": [
            "Faire revenir l'oignon, le céleri et l'ail dans le beurre 5 min.",
            "Ajouter le bouillon, le poulet, le persil et le macaroni.",
            "Mijoter jusqu'à cuisson complète (8 à 10 min).",
            "Ajuster avec de l'eau si nécessaire en fin de cuisson.",
        ],
    },
    # --- page 5 (101205) ---
    {
        "src": "20260503_101205.heic",
        "title": "Soupe tomates et orge (6 à 8 pers.)",
        "ingredients": [
            "huile d'olive, 2 gros oignons",
            "1 boîte de bouillon de bœuf",
            "2 t. d'eau, 1 boîte de jus tomates V8",
            "2 boîtes de tomates en dés (ou jus)",
            "1 c. à soupe de sucre brun, persil, basilic",
            "ail, échalote, herbes mélangées",
            "1 boîte tomates, 5 min, en bouillon, ajouter orge",
            "1 tasse jusqu'à 1 c. à thé sel, sirop, longtemps, sel, poivre",
            "Mai si non commencer par une boîte de tomate",
        ],
        "steps": [
            "Faire revenir l'oignon dans l'huile, ajouter le bouillon, les tomates, l'orge et le sucre.",
            "Ajouter les fines herbes (basilic, persil).",
            "Mijoter longtemps (1 h+), saler et poivrer.",
        ],
    },
    {
        "src": "20260503_101205.heic",
        "title": "Soupe courge bouillie",
        "ingredients": [
            "1 oignon, 2 courges, 1 morceau de gingembre",
            "1 cube de bouillon de poulet",
            "huile d'olive, sel, poivre",
            "1 c. à thé de chili, 2 c. à soupe de basilic",
            "1 c. à soupe de pommes de terre en dés",
            "1 boîte de mais (1 doigt)",
            "Mélangeur, et servir",
        ],
        "steps": [
            "Faire revenir l'oignon dans l'huile, ajouter la courge en dés et le gingembre râpé.",
            "Ajouter le bouillon, le chili, le basilic et la pomme de terre.",
            "Mijoter jusqu'à tendreté, ajouter le mais.",
            "Passer au mélangeur, sel et poivre.",
        ],
    },
    {
        "src": "20260503_101205.heic",
        "title": "Mes deux soupes à la famille (4 grosses soupes)",
        "ingredients": [
            "1 boîte de tomates en dés (28 oz), 3 1/2 tasses d'eau",
            "1 carcasse / bouillon de poulet ou bouillon de poulet, 5 carcasses",
            "5 grosses carottes coupées, 1 1/2 t. de chou vert, sel, poivre",
            "3 branches céleri, sel, poivre, persil",
            "(continue sur page suivante)",
        ],
        "steps": [
            "Mettre tous les ingrédients dans une grande marmite.",
            "Amener à ébullition, baisser et mijoter 1 h 30 à 2 h.",
            "Saler, poivrer, servir avec persil frais.",
        ],
    },
    # --- page 6 (101219) ---
    {
        "src": "20260503_101219.heic",
        "title": "Mes deux soupes (suite) — bouillon parfumé",
        "ingredients": [
            "Mes herbes salées (ce que j'ai en supplément)",
            "3/4 c. à thé de poivre haché, 1/2 t. ail",
            "1 boîte d'arômes de bouillon Vegeta",
            "1 carcasse de tomates V8 (4 fois)",
            "soupe à l'oignon, bouillon de poulet",
            "ajouter carotte, chou, navet, céleri",
            "cuire à feu doux 2 heures",
            "15 min avant fin de cuisson, ajouter pâte alimentaire",
            "P.B. soupes d'épices, herbes, bouillon de poulet, longue",
        ],
        "steps": [
            "Réunir tous les ingrédients dans une grande marmite.",
            "Cuire à feu doux pendant 2 heures.",
            "Ajouter les pâtes alimentaires 15 min avant la fin de cuisson.",
        ],
    },
    {
        "src": "20260503_101219.heic",
        "title": "Soupe poulet et riz",
        "ingredients": [
            "1 c. à thé d'huile, 1 1/2 t. de riz, oignon, persil",
            "1/2 t. de carottes en dés, 1 c. à thé de bouillon de poulet en poudre",
            "1 oignon haché, fines herbes au goût",
            "4 t. de bouillon de poulet, 3 t. d'eau",
            "3/4 tasse riz, 1/4 t. lait, 1 t. de poulet",
            "cuit en dés, sel, poivre",
        ],
        "steps": [
            "Chauffer l'huile, faire revenir l'oignon, les carottes et l'ail.",
            "Ajouter l'assaisonnement, le bouillon, l'eau et le riz.",
            "Mijoter et chauffer, baisser et cuire à feu doux jusqu'à ce que le riz soit cuit.",
            "Ajouter le poulet en dés, sel et poivre.",
        ],
    },
    # --- page 7 (101227) ---
    {
        "src": "20260503_101227.heic",
        "title": "Potage d'hiver à pois pour cousin",
        "ingredients": [
            "1 c. à soupe d'huile, 1 échalote française hachée",
            "1 oignon en cubes (environ 1 patate)",
            "4 t. bouillon de poulet, 1 fenouil, 2 c. à soupe de basilic",
            "1 boîte (28 oz) tomates, sel, poivre",
            "Casserole, faire revenir oignon et échalote 5 min.",
            "Ajouter sel, légumes, mijoter 5 min.",
            "Ajouter bouillon de poulet, sel, poivre, fines herbes.",
            "Mijoter 20 min, ajouter pois.",
            "Encore 15 min, blender.",
            "Ajouter le bouillon de poulet si trop épais, à servir avec des croûtons de pain.",
        ],
        "steps": [
            "Faire revenir l'oignon et l'échalote 5 min dans l'huile.",
            "Ajouter sel et légumes, mijoter 5 min.",
            "Ajouter bouillon de poulet, sel, poivre et fines herbes.",
            "Mijoter 20 min, ajouter les pois.",
            "Encore 15 min, passer au blender.",
            "Ajuster avec du bouillon si trop épais, servir avec des croûtons de pain.",
        ],
    },
    {
        "src": "20260503_101227.heic",
        "title": "Soupe santé à l'orge",
        "ingredients": [
            "3/4 t. d'orge mondé",
            "1 carotte fine en dés",
            "1 branche de céleri en dés",
            "1 oignon fin",
            "1 navet fin émincé",
            "3 g. d'ail émincé",
            "2 t. de bouillon de poulet",
            "3 t. d'eau, 1 c. à thé de pâte de tomate",
            "1/2 t. orge épongée (ou trempée 1 h)",
            "1 t. d'oignon vert, 3/4 c. à thé de cumin",
            "sel, poivre",
            "1 t. d'oignon vert, 3/4 c. à thé de cumin, 4 c. à soupe de persil",
        ],
        "steps": [
            "Faire revenir l'oignon, l'ail, la carotte, le céleri et le navet.",
            "Ajouter le bouillon de poulet, l'eau et la pâte de tomate.",
            "Ajouter l'orge, mijoter 1 h 30 à 2 h.",
            "Saler, poivrer, ajouter cumin et persil avant de servir.",
        ],
    },
    # --- page 8 (101237) ---
    {
        "src": "20260503_101237.heic",
        "title": "Crème de brocoli",
        "ingredients": [
            "2 c. à soupe de beurre, 1 oignon haché",
            "1 g. d'ail, 1 brocoli coupé fin",
            "2 c. à soupe de bouillon de poulet, 4 t. d'eau",
            "2 c. à soupe de beurre, 2 c. à soupe de farine",
            "2 t. de lait ou 1 1/2 t. de lait et 1/2 t. de crème",
            "lait évaporé, poivre, sel",
            "1 1/2 t. de fromage Velveeta (ne pas omettre)",
            "Fondre le beurre, ramollir oignon, ail, céleri, ajouter brocoli,",
            "tomate, crème, mijoter pour réduire au blender.",
            "Sans une sorte de cocotte fond minuté, sans une petite sorte de pâté de tomate, ajouter sel ou tomate jusqu'à le café.",
            "Mélanger et verser dans la soupe, ajouter le fromage, servir.",
        ],
        "steps": [
            "Fondre le beurre, ramollir oignon, ail, céleri.",
            "Ajouter brocoli et tomate, mijoter pour réduire.",
            "Passer au blender.",
            "Faire un roux dans une cocotte, ajouter au mélange.",
            "Verser dans la soupe, ajouter le fromage, servir.",
        ],
    },
    {
        "src": "20260503_101237.heic",
        "title": "Soupe bœuf et orge mondé",
        "ingredients": [
            "1 1/2 lb de bœuf en cubes, 5 t. d'eau",
            "1 c. à soupe d'huile, 1 oignon, 2 carottes en dés",
            "1 c. à thé de pâte de tomate, 1 c. à thé de Marmite",
            "1/2 t. d'orge mondé, sel, poivre",
            "ail, thym, laurier",
            "Faire revenir le bœuf dans l'huile 5 min.",
        ],
        "steps": [
            "Faire revenir le bœuf en cubes dans l'huile 5 min.",
            "Ajouter l'oignon, les carottes et faire revenir.",
            "Couvrir d'eau, ajouter la pâte de tomate, la Marmite, l'orge et les fines herbes.",
            "Mijoter 1 h 30 à 2 h jusqu'à ce que le bœuf et l'orge soient tendres.",
        ],
    },
    # --- page 9 (101247) ---
    {
        "src": "20260503_101247.heic",
        "title": "Soupe à la dinde",
        "ingredients": [
            "1 c. à soupe d'huile, 1 oignon en dés",
            "1 carotte en dés, 1 céleri en dés",
            "2 c. à soupe d'assaisonnement italien Pasco",
            "1 carcasse de dinde (ou 1 dinde) avec carcasse",
            "1 t. de chou rappé, 6 t. de bouillon de dinde",
            "Cuire 1 h, ajouter sel, poivre",
            "1 t. de soupe au tomate (28 oz)",
        ],
        "steps": [
            "Chauffer l'huile, faire revenir l'oignon, la carotte, le céleri et l'ail.",
            "Ajouter l'assaisonnement italien, la carcasse de dinde et l'eau.",
            "Mélanger, mijoter et faire fondre.",
            "Cuire environ 1 h, retirer la carcasse, ajuster, ajouter du bouillon si nécessaire.",
        ],
    },
    {
        "src": "20260503_101247.heic",
        "title": "Soupe à l'orge facile",
        "ingredients": [
            "1 oignon en dés, 3 lb. de bœuf",
            "1 jambon coupé à l'oignon, 1 poivron, 3 c. à soupe d'huile",
            "1 c. à thé de café, bouillon ou poudre, 4 t. d'eau",
            "1/2 c. à thé de gingembre, 1/2 c. à thé de thym",
            "1/3 c. à thé de basilic, 1/2 t. d'orge mondé, 1 boîte de tomate en dés",
            "tomate en dés, 4 c. à soupe de céleri",
        ],
        "steps": [
            "Faire revenir le jambon, l'oignon et le poivron 5 min.",
            "Ajouter le bouillon, l'eau, les fines herbes et l'orge.",
            "Ajouter les tomates, mijoter 1 h.",
            "Saler, poivrer et servir.",
        ],
    },
    # --- page 10 (101300) ---
    {
        "src": "20260503_101300.heic",
        "title": "Soupe poulet à l'orge",
        "ingredients": [
            "3 t. de bouillon de poulet (5 1/2 t.)",
            "3/4 t. d'orge perlé",
            "Faire tremper l'orge dans l'eau 30 min.",
            "1 oignon, bouillon de poulet, eau, sel, poivre",
            "1 carotte, chaudron à un, ajouter le poulet,",
            "Cuire 30 min, ajouter au mélange,",
            "1 tomate, ajouter sel, poivre",
            "1 jusqu'à cuit, ajouter eau s'il faut.",
            "Bonne soupe sapeurs, à le congeler bien.",
        ],
        "steps": [
            "Tremper l'orge dans l'eau 30 min.",
            "Faire revenir l'oignon dans l'huile, ajouter la carotte.",
            "Ajouter le poulet et cuire 30 min.",
            "Ajouter l'orge égoutté, le bouillon, mijoter 1 h.",
            "Saler, poivrer et servir.",
        ],
        "notes_extra": "Bonne soupe pour la congélation.",
    },
    {
        "src": "20260503_101300.heic",
        "title": "Soupe (Mindies — Chine)",
        "ingredients": [
            "5 oignons (3 tasses émincées)",
            "2 c. à soupe de beurre",
            "5 t. de bouillon de poulet ou autre",
            "Bordelais (12 onces / 341 ml), 5 t. de lait, 4 t. de bouillon de poulet, feuilles de laurier",
            "1 c. à thé de thym, 2 c. à thé de Maggie",
            "30 min, soupe avec laurier, croûtons et fromage gratiné au four — servir",
        ],
        "steps": [
            "Faire fondre le beurre, ajouter les oignons émincés, cuire à feu doux jusqu'à caramélisation (30 min).",
            "Ajouter le bouillon, le lait, les feuilles de laurier, le thym et la sauce Maggie.",
            "Mijoter 30 min, retirer les feuilles de laurier.",
            "Servir avec croûtons et fromage gratiné au four.",
        ],
    },
    {
        "src": "20260503_101300.heic",
        "title": "Soupe reste de dinde",
        "ingredients": [
            "1 oignon, 1 tomate, 1 persil",
            "3 boîtes de bouillon de poulet, 1 t. de pâte de tomate",
            "1 oignon en cubes, 3 carottes en dés",
            "3 g. d'ail, 1 t. de céleri en dés (ou pas fin)",
            "déjà cuit, 1 t. de viande au fond,",
        ],
        "steps": [
            "Faire revenir l'oignon, le céleri et l'ail.",
            "Ajouter le bouillon, les carottes et la pâte de tomate.",
            "Ajouter la viande de dinde restante, mijoter 1 h.",
            "Saler, poivrer et servir.",
        ],
    },
    # --- page 11 (101317) ---
    {
        "src": "20260503_101317.heic",
        "title": "Gibelotte de Sorel",
        "ingredients": [
            "1 lb de bœuf salé ou bardotte",
            "1 oignon coupé fin, huile",
            "6 patates coupées, 1 lb de jambon",
            "1 1/2 t. de pâte de tomate, 1/2 c. à soupe de sirop d'érable",
            "1 boîte tomate, 1 t. de bouillon de poulet",
            "2 t. mais en grain, 1 1/2 t. d'haricots",
            "1 t. fèves rouges, 3 carottes, sel, poivre",
            "feuilles de laurier, thym, persil",
            "tomate, sel de céleri, sel, poivre",
            "3 lbs de poulet désossé en pièces",
            "rincer et parer dans le bouillon",
            "dans une marmite, 10 lt (40 tasses)",
            "ajouter oignon, cuire, ajouter",
            "patate, carotte, oignon, cuire 10 à 12 min, ajouter pâte de tomate, sirop, tomate, mais",
            "haricots et jus, ajouter l'heure",
            "Ajouter pâté de fèves, chaude, sur place",
            "Cuire 1 min, ajouter les fines",
            "Ajouter le jus haché, écraser",
            "à la pâté de farine, sel, poivre",
            "(une autre soupe complète sur cuisson)",
            "fond et ensuite déposer la marmite",
        ],
        "steps": [
            "Faire revenir le bœuf et le jambon dans l'huile.",
            "Ajouter l'oignon, les carottes, les patates et le poulet désossé.",
            "Ajouter la pâte de tomate, le sirop d'érable, les tomates, le bouillon, le mais et les haricots.",
            "Mijoter longtemps avec fines herbes (laurier, thym, persil), sel et poivre.",
            "Servir avec pâté de farine si désiré.",
        ],
    },
    # --- page 12 (101327) ---
    {
        "src": "20260503_101327.heic",
        "title": "Soupe poulet et boulettes",
        "ingredients": [
            "Poulet en morceaux 6 1/2 lb, 1 boîte",
            "poulet de pâte en macaroni, 1 1/2 t. de bouillon",
            "lentilles d'eau, 1 t. farine, 3 g. d'ail",
            "Champignons en boîte, 1 t. paprika de bœuf, 1 t. de Tabasco, ail, persil, fines herbes",
            "1 patate en dés, 1 1/4 c. à thé de sel, 1 1/4 c. à thé de poivre",
            "1 chou-fleur, 2 t. farine, 4 c. à thé poudre, 1 c. à thé sel",
            "Boulettes — 3/4 t. de gras de bœuf, 2 c. à thé farine",
            "Roulettes laine fondue — 3/4 c. à thé baisser",
            "Placez poulet, eau, bouillon, fond gras, ail dans casserole.",
            "Cuire ébullition baisser la température, écumer, mijoter 60 min.",
            "Retourner la bouillie, désosser à la marmite. Retirer fond jusqu'à 4 fois, désosser. Cuire en morceaux. Couler la bouillie en cassant la peau. Remettre poulet dans la casserole, ajouter la bouillie, écumer.",
            "Préparer la jardinière. Suivre les instructions des fines herbes. Ajouter les boulettes dans la marmite. Boulettes — Mélanger lait, œuf, beurre fondu, sel, poivre. Pour la pâte, mêler farine et moelle, faire un puits, ajouter mélange, mélanger.",
        ],
        "steps": [
            "Placer poulet, eau, bouillon et ail dans casserole, mijoter 60 min, désosser.",
            "Préparer les légumes (oignon, céleri, carottes, chou-fleur, patate), ajouter au bouillon avec fines herbes, sel et poivre.",
            "Pour les boulettes, mélanger lait, œuf, beurre fondu, sel, poivre, puis incorporer farine et moelle.",
            "Déposer les boulettes par cuillerées dans la soupe bouillante, couvrir et cuire 15 min.",
        ],
    },
    # --- page 13 (101335) ---
    {
        "src": "20260503_101335.heic",
        "title": "Soupe au poulet",
        "ingredients": [
            "1 oignon, 5 branches de céleri",
            "1 t. de poulet cuit, 1 t. de jambon cuit",
            "12 tomates, 1 t. d'eau (3 litres), sel, poivre",
            "pâte de poulet cuit, 1 1/2 c. à thé de sucre",
            "1/4 t. à 1 t. mijoter avec ajustement",
            "Pour cuit en train à riz, écraser avec un mélanger ou écraser avec...",
        ],
        "steps": [
            "Faire revenir oignon et céleri.",
            "Ajouter les tomates, l'eau et le bouillon de poulet.",
            "Ajouter le poulet et le jambon en morceaux.",
            "Mijoter, saler, poivrer. Ajouter le riz si désiré, mijoter jusqu'à cuisson.",
        ],
    },
    {
        "src": "20260503_101335.heic",
        "title": "Soupe poulet (style mère)",
        "ingredients": [
            "3 1/2 lb de poulet, 8 morceaux",
            "12 t. d'eau, 1 grosse carotte en dés",
            "1 gros oignon en dés, 1 oignon en dés, 1 grosse",
            "branche de céleri en dés, 1 oignon haché",
            "2 c. à soupe sel cassher, 1 cube bouillon",
            "poulet, 1 c. à soupe gros sel, 15 min de persil, 1 lb d'olives",
            "soupe entière, 6 oz de poulet une",
            "fois bouillon clair, ajouter la légume sel, bouillon en cube. Mijoter à",
            "couvert 1 h 30. Cuire 15 dernières minutes ajouter, longuement écumer",
            "à l'écumoire, poulet, mettre fond d'eau dans soupe. Verser la soupe et",
            "le jus sur le poulet.",
        ],
        "steps": [
            "Mettre poulet, eau, oignon, céleri, persil, sel et bouillon dans une grande marmite.",
            "Cuire à découvert jusqu'à ce que le bouillon soit clair (écumer régulièrement).",
            "Ajouter les légumes, mijoter à couvert 1 h 30.",
            "Cuire 15 dernières minutes, écumer, retirer le poulet.",
            "Servir poulet et bouillon ensemble.",
        ],
    },
    # --- page 14 (101345) ---
    {
        "src": "20260503_101345.heic",
        "title": "Soupe de poisson",
        "ingredients": [
            "500 g de morue ou merlan",
            "500 g de crevettes roses crues",
            "2 patates, 1 oignon, 3 c. à soupe pâte",
            "de tomate, 2 c. à soupe fumet de",
            "poisson, 1 litre d'eau, jus d'un citron",
            "ou de Cayenne, bouquet garni, sel, poivre",
            "Dans 1 grand chaudron, revenir oignon et",
            "poisson coupé, ajouter les patates,",
            "tomate, fumet, eau, ébullition, fond, mijoter 30",
            "Ajouter poisson, pâte de tomate, cuire jusqu'à ce que le poisson soit cuit, mijoter 2 h 30 en fond.",
        ],
        "steps": [
            "Dans un grand chaudron, faire revenir l'oignon dans l'huile.",
            "Ajouter les patates en dés, la pâte de tomate, le fumet de poisson et l'eau.",
            "Porter à ébullition, mijoter 30 min.",
            "Ajouter le poisson et les crevettes, cuire 5 à 10 min.",
            "Saler, poivrer, ajouter jus de citron et bouquet garni.",
        ],
    },
    {
        "src": "20260503_101345.heic",
        "title": "Soupe crémeuse jambon-patate",
        "ingredients": [
            "1/2 t. de beurre, 1 oignon fin, 1 t. céleri en dés",
            "1/2 céleri en dés, 3 patates en dés",
            "1/2 g d'ail, 1/2 t. patate en dés",
            "3 t. de lait, 1 pincée de sel",
            "céleri vert, 1 jaune oignon, carotte",
            "patate, eau, oignon, pâte d'ail, sel",
            "30 min, jambon et céleri en dés 2 min,",
            "1 farine, ajouter et cuire 2 min",
            "le feu à ébullition jusqu'à pommes de terre",
            "tendres, 10 à 12 min",
        ],
        "steps": [
            "Faire fondre le beurre, ajouter oignon, céleri et ail, cuire jusqu'à transparent.",
            "Ajouter pommes de terre, eau, sel, mijoter 30 min.",
            "Ajouter jambon en dés et céleri 2 min, saupoudrer de farine, cuire 2 min.",
            "Verser le lait, mijoter à feu doux jusqu'à ce que les pommes de terre soient tendres (10 à 12 min).",
        ],
    },
    # --- page 15 (101358) ---
    {
        "src": "20260503_101358.heic",
        "title": "Soupe Bangkok comme au restaurant",
        "ingredients": [
            "2 c. à soupe huile, 3 g. d'ail fin",
            "1 oignon en lanières, 3 t. de bouillon de poulet, 1 t. de poulet cuit, 3 1/4 t. lait coco",
            "1 1/2 c. à soupe pâte de cari rouge, en plus de boullie, 1 c. à soupe de pâte de cari",
            "rouge, 1 c. à thé sel, 3 c. à soupe de sucre",
            "coriandre, 1 paquet vermicelles de riz",
            "Chauffer l'huile, sucre, oignon ce qui est doré, jusqu'à ne pas brunir.",
            "Ajouter le cari, crème, sucre, ajouter le lait coco, mijoter, bouillon de poulet, mais doucement, lait de coco. Pâte tout. Bouillir, ajouter sucre, coriandre, lime",
            "ajouter sel et 1 t. d'eau pour dernière 1 t.",
            "graduellement saler. Pour avec poivre, légèrement, Mijoter, cuire vermicelle couper à 2 fois environ bien dans le bouillon. Vermicelle. C'est si difficile de ramasser dans le fond.",
            "Coriandre.",
        ],
        "steps": [
            "Chauffer l'huile, faire revenir l'oignon doré sans brunir.",
            "Ajouter la pâte de cari, mijoter avec le bouillon et le lait de coco.",
            "Ajouter le sucre, le sel, le jus de lime et la coriandre.",
            "Ajouter le poulet cuit, ajuster avec de l'eau si nécessaire.",
            "Cuire les vermicelles de riz à part, les couper en deux et les ajouter à la soupe au moment de servir.",
        ],
    },
    # --- page 16 (101409) ---
    {
        "src": "20260503_101409.heic",
        "title": "Crème de céleri (chez Lina ou dame)",
        "ingredients": [
            "huile d'olive et beurre",
            "céleri en dés, feuilles et tige",
            "1 oignon, 1 poireau émincé, 1 g. d'ail",
            "1 pomme de terre en rondelles",
            "1/2 c. à thé de cardamome, 1 c. à thé de moutarde",
            "basilic, sel, poivre, chauffer 2 c. à soupe huile et beurre, oignons en morceaux",
            "ajouter les légumes, faire revenir quelques minutes, déposer ensuite l'eau, mijoter doucement 20 min, jusqu'à c'est tendre, légumes",
            "ajouter la crème, mijoter, ajouter dans la crème, mijoter, déposer pour avant servir.",
        ],
        "steps": [
            "Chauffer huile et beurre, faire revenir l'oignon et le poireau.",
            "Ajouter l'ail, le céleri, la pomme de terre, la cardamome, la moutarde et le basilic.",
            "Ajouter de l'eau, mijoter 20 min jusqu'à tendre.",
            "Passer au mélangeur, ajouter la crème, mijoter, sel et poivre.",
        ],
    },
    {
        "src": "20260503_101409.heic",
        "title": "Soupe nourrissante",
        "ingredients": [
            "1 oignon en dés, 4 carottes en dés",
            "3 carottes en dés, 1 c. à thé d'huile",
            "2 g. d'ail fin, 2 c. à soupe d'huile d'olive",
            "saler, poivre, 1 fenouil champignons, persil",
            "2 oignon hachés au goût, 1 t. de pâte poulet, en",
            "moelle ou ramolli au goût, 1 t. de bouillon",
            "de bœuf, 1 oz de bouillon de poulet, mettre 1 t. de bœuf",
            "Mettre tomate, persil, poireau, mijoter, fond,",
            "ajouter à couvert 1 h, ajouter du",
            "champignons et celui sur le pâté, mijoter, vapeur",
            "Saler ou en concassé, 5 ou ramolli au pâté, en, ouvre",
            "Pour ces 5 ramolli ou Chauffer feu",
            "moyen, ajouter, légumes, poulet, fines herbes",
            "10 min, ajouter orge ou nouilles, poulet, gnocchi, pomme",
            "de terre",
        ],
        "steps": [
            "Faire revenir l'oignon, les carottes et l'ail dans l'huile.",
            "Ajouter le fenouil, les champignons, le persil et le bœuf en morceaux.",
            "Ajouter le bouillon, mijoter à couvert 1 h.",
            "Ajouter les fines herbes 10 min avant la fin.",
            "Ajouter orge, nouilles ou gnocchi de pomme de terre selon goût.",
        ],
    },
    # --- page 17 (101421) ---
    {
        "src": "20260503_101421.heic",
        "title": "Soupe maman (Marie)",
        "ingredients": [
            "5 grosses carottes, 4 patates en lamelle",
            "oignon en morceaux, 1 jambon coupé",
            "en morceaux, 2 c. à soupe de beurre",
            "1 feuille de laurier, 1 c. à soupe de basilic",
            "ou 1 c. à thé thym, 1 c. à thé de basilic",
            "8 t. bouillon de poulet, 3 1/2 t. à",
            "2 t. de lait, sel, poivre",
            "1/2 t. fromage râpé, 1/2 c. à thé poivre",
            "en passant ajouter à la fin de cuisson, 1 t. fromage râpé",
            "porter à ébullition, ajouter pour deux minutes",
            "1 heure, retirer la feuille de laurier, passer au mélangeur, ramollir",
            "des cerises, ajouter le fromage à la touche de soupe et quelques croûtons à la touche",
            "de lait consistance désirée",
        ],
        "steps": [
            "Faire revenir l'oignon et le jambon dans le beurre.",
            "Ajouter carottes, pommes de terre, fines herbes, bouillon et lait.",
            "Mijoter 1 h, retirer la feuille de laurier.",
            "Passer au mélangeur, ajouter le fromage râpé, ajuster avec lait au goût.",
        ],
    },
    {
        "src": "20260503_101421.heic",
        "title": "Soupe légère de Tata B.",
        "ingredients": [
            "1 boîte tomates 28 oz, 3 lt d'eau",
            "1 jambon coupé l'oignon, 1 oignon",
            "3 c. à thé cuilli/bouillon, fenouille en poudre",
            "5 grosses carottes (avec 4), 1 1/2 t. de chou râpé",
            "3 branches céleri fin, sel, poivre",
            "3/4 c. à thé fines herbes, 1/2 t. pâte alimentaire",
            "à soupe avec cube",
            "Cuire 2 h en feu doux 1 1/2 oz avant",
            "fin de cuisson ajouter pâte alimentaire 15",
            "à fin alimentaire",
        ],
        "steps": [
            "Mettre tomates, eau, jambon, oignon, bouillon, fenouille en poudre, carottes, chou et céleri dans une grande marmite.",
            "Saler, poivrer, ajouter fines herbes.",
            "Cuire à feu doux 2 h.",
            "Ajouter pâte alimentaire 15 min avant la fin.",
        ],
    },
    # --- page 18 (101429) ---
    {
        "src": "20260503_101429.heic",
        "title": "Soupe tomate à vermicelle",
        "ingredients": [
            "4 t. bouillon de jambon, 1 jus de tomate",
            "2 g. d'ail, 1 oignon, 1 grosse carotte",
            "1 branche de céleri, 3/4 t. d'écorce de melon",
            "sel, poivre",
        ],
        "steps": [
            "Mettre bouillon, jus de tomate, ail, oignon, carotte et céleri dans une casserole.",
            "Mijoter, saler et poivrer.",
            "Ajouter vermicelle vers la fin, cuire jusqu'à tendre.",
        ],
    },
    {
        "src": "20260503_101429.heic",
        "title": "Autre soupe tomate au céleri",
        "ingredients": [
            "2 c. à soupe de beurre, 1 oignon en dés",
            "2 g. d'ail, 1 t. de céleri en dés",
            "2 branches céleri en dés, 1 1/2 t. de bouillon",
            "(ou 1 boîte) 28 onces de boîte d'huile",
            "en cubes, 1 c. à thé sel",
            "1 c. à soupe pâte de tomate, 1 lb pâte",
            "Tomate 540 ml, 8 t. bouillon poulet",
            "ou poulet, 1 c. à thé pâte tomate",
            "1/2 c. à soupe sucre, sel, poivre, persil",
            "vers la fin, 1 cube, 40 min au feu",
            "Crème 40 min au feu",
        ],
        "steps": [
            "Faire fondre le beurre, faire revenir l'oignon, l'ail et le céleri.",
            "Ajouter le bouillon, la pâte de tomate, le sel et le sucre.",
            "Mijoter 40 min.",
            "Ajouter persil et crème vers la fin.",
        ],
    },
    {
        "src": "20260503_101429.heic",
        "title": "Soupe maison de fenouil",
        "ingredients": [
            "1/2 t. beurre, 1 oignon, 4 c. à soupe",
            "de carottes en dés, 4 t. bouillon de bœuf",
            "15 ml de farine grillée, 1/2 t. vin rouge",
            "4 t. bouillon poulet, 1 fenouil émincé",
            "feuilles persil",
        ],
        "steps": [
            "Faire fondre le beurre, ajouter l'oignon et les carottes.",
            "Saupoudrer de farine grillée.",
            "Ajouter le bouillon de bœuf, le vin rouge, le bouillon de poulet et le fenouil.",
            "Mijoter, garnir de feuilles de persil.",
        ],
    },
    {
        "src": "20260503_101429.heic",
        "title": "Chaudrée de palourdes (autre version)",
        "ingredients": [
            "Houde de palourdes en morceaux",
            "1 oignon en cubes, 2 céleri en dés",
            "1/4 t. de beurre, 3 c. à soupe de farine",
            "2 t. de lait, 1/2 c. à soupe de tomate",
            "1 cube de tournesol, soda émietté, 3 t. de",
            "patates cuites en dés, 1 1/2 t. de crème",
            "sel, poivre",
        ],
        "steps": [
            "Faire fondre le beurre, faire revenir l'oignon et le céleri.",
            "Ajouter la farine, mélanger.",
            "Ajouter le lait, la pâte de tomate, le bouillon, mijoter.",
            "Ajouter les palourdes, les patates cuites et la crème.",
            "Saler, poivrer, servir avec biscuits soda émiettés.",
        ],
    },
    # --- page 19 (101441) ---
    {
        "src": "20260503_101441.heic",
        "title": "Crème de tomate au cumin (Nathalie Champinski)",
        "ingredients": [
            "1 c. à soupe de beurre, 1 oignon ciselé",
            "1 oignon moyen, 4 patates pelées en dés",
            "ou environ, 4 t. d'eau, 2 c. à soupe gingembre",
            "frais, 1 boîte de tomates en cubes (790 ml)",
            "1 c. à soupe sel, 1 t. de bouillon de poulet",
            "1 pincée de Sucro, sel, poivre, 1/2 t. de",
            "crème 35%, filet de crème pour décor, ciboulette ou jaroti(?)",
            "Fondre la base, ajouter l'oignon, mijoter, oignon, ginger, ail, mijoter, ajouter la pâte",
            "10 min ou jusqu'à c'est tendre, ajouter les tomates, l'eau, la pâte, le sel et le bouillon, mijoter, ajuster avec eau, ajouter cumin et coriandre, faire à feu doux, mijoter 30 min.",
            "Blender, ajouter cumin et coriandre, ajuster avec eau si trop épais, ajouter crème, sel, poivre.",
            "Servir avec sel à soupe et garnir avec un filet de crème (Nathalie Champinski).",
        ],
        "steps": [
            "Fondre le beurre, ajouter l'oignon, mijoter.",
            "Ajouter les patates, le gingembre, les tomates, l'eau et le bouillon.",
            "Mijoter 30 min, ajouter cumin et coriandre.",
            "Passer au blender, ajuster avec de l'eau si trop épais, ajouter la crème.",
            "Saler, poivrer, garnir d'un filet de crème et de ciboulette.",
        ],
    },
    {
        "src": "20260503_101441.heic",
        "title": "Soupe au cheddar",
        "ingredients": [
            "3 t. de bouillon, 1 oignon, 4 patates en dés",
            "1 céleri haché, 1 carotte en dés",
            "1/2 t. d'oignon haché, 1 louche de farine au tiers",
            "sel, poivre, 2 t. fromage au lait, 1/2 t. de",
            "lait au fromage, 1 c. à thé de basilic",
            "rouge (455 g) ou autre sorte ou crouton",
        ],
        "steps": [
            "Faire revenir oignon, céleri et carotte.",
            "Ajouter bouillon, patates, mijoter jusqu'à tendre.",
            "Ajouter farine, lait et fromage râpé.",
            "Saler, poivrer, ajouter basilic.",
        ],
    },
    # --- page 20 (101448) ---
    {
        "src": "20260503_101448.heic",
        "title": "Crème oignon (style camerounais ?)",
        "ingredients": [
            "5 oignons hachés, 2 c. à soupe huile d'olive",
            "6 t. bouillon poulet, 3 feuilles de thym",
            "ou 1 c. à thé thym, 1 1/2 t. fromage cheddar fort",
            "1 morceau, 1 c. à thé huile, 1 forme soupe à l",
            "à soupe ciboulette",
            "1 oignon en dés, 1 c. à thé d'huile,",
            "5 oignons cuits, 1 t. mais en grain",
            "Crème oignon, 1 t. à 1 t. de soupe à",
            "10 min ou jusqu'à attendrir,",
            "oignons dans 1 huile, 10 min ou jusqu'à",
            "bouillon, patates, mijoter 10 min",
            "jusqu'à tendre, blender, passer au filtre",
            "tamis, sel, poivre, ajouter de la",
            "crème, ajouter formage, jusqu'à fond,",
            "ferme, vinaigre Dijon, soda u 1 1/2 t.",
            "et reste de l'huile, servir la soupe",
        ],
        "steps": [
            "Faire revenir les oignons dans l'huile environ 10 min jusqu'à attendris.",
            "Ajouter bouillon et patates, mijoter 10 min jusqu'à tendre.",
            "Passer au mélangeur (blender), tamiser, saler et poivrer.",
            "Ajouter crème et fromage cheddar fort.",
            "Ajouter ciboulette et le vinaigre Dijon avant de servir.",
        ],
    },
    # --- page 21 (101459) ---
    {
        "src": "20260503_101459.heic",
        "title": "Soupe carottes et oignons",
        "ingredients": [
            "3 c. à soupe beurre, 4 t. oignons en lanières",
            "1 force sel, 4 t. carottes en rondelles",
            "1 t. tomates, 1 c. à soupe de bouillon de poulet",
            "8 c. à soupe de bouillon de poulet, 1 carotte",
            "1 t. eau, 1/2 t. lait, ajusté à thé",
            "1 oz, ajouter blender, verser le faire pour",
            "garder de courbes à pieds",
        ],
        "steps": [
            "Faire fondre le beurre, ajouter oignons et carottes.",
            "Saler, poivrer, ajouter bouillon, tomates, eau et lait.",
            "Mijoter jusqu'à tendre.",
            "Passer au blender, garnir et servir.",
        ],
    },
    {
        "src": "20260503_101459.heic",
        "title": "Bouillabaisse au poireau et fenouil",
        "ingredients": [
            "1 gros oignon en dés, 1 boîte de fenouil",
            "en cubes, 2 branches de céleri",
            "fennel ou cubes en dés en cubes",
            "2 carottes, 2 g. d'ail, 1 c. à soupe d'huile",
            "8 anis vert, 5 c. à thé thym (ou ailes), 1 c. à thé",
            "1 c. à thé poudre, 1/2 t. vin blanc",
            "sec, 1 t. jus de palourdes ou bouillon",
            "de poulet, 1/2 c. à thé safran moulu, 1 c. à thé",
            "soupe pâte de tomate, sel, poivre",
            "1 sel poivre, 1 fish, 1 lbs en sole, 1/2 lbs",
            "en cubes, 1 t. de moules, 1/2 lb de calamars",
            "en moules, 12 grosses crevettes, 12",
            "lb de poireau, 1 c. à soupe de céleri",
            "Dans une casserole, faire revenir l'oignon",
            "le fenouil, le céleri, les carottes",
            "ail, persil, ciboulette dans l'huile, ajouter pâte de tomate, mijoter, ajouter vin blanc, jus de palourdes, safran, sel, poivre. Mijoter 40 min, ajouter le poisson, palourdes, calamars, mijoter 20 min, ajouter crevettes, cuire 5 min de plus, garnir.",
        ],
        "steps": [
            "Dans une casserole, faire revenir oignon, fenouil, céleri, carottes et ail dans l'huile.",
            "Ajouter pâte de tomate, vin blanc, jus de palourdes, safran, sel et poivre.",
            "Mijoter 40 min.",
            "Ajouter poisson, moules et calamars, mijoter 20 min.",
            "Ajouter les crevettes, cuire 5 min de plus.",
            "Garnir et servir.",
        ],
    },
    # --- page 22 (101514) ---
    {
        "src": "20260503_101514.heic",
        "title": "Soupe poulet maison",
        "ingredients": [
            "Poulet cuit en petits morceaux",
            "1 oignon, 4 patates en cubes",
            "1 céleri, 2 carottes en dés",
            "1 boîte tomate, 4 t. de bouillon de poulet",
            "1 lb de viande, 1 g. d'ail fin",
            "1/2 c. à thé de basilic",
            "1 1/2 t. de pâte de tomate, 1/4 c. à soupe de sel",
            "Casserole, mijoter 30 min, sel, poivre",
            "Ajouter en cours, sel, poivre",
            "(continue dans recette suivante)",
        ],
        "steps": [
            "Mettre poulet, légumes, tomate et bouillon dans une casserole.",
            "Ajouter ail, basilic, pâte de tomate, sel et poivre.",
            "Mijoter 30 min, ajuster les assaisonnements.",
        ],
    },
    {
        "src": "20260503_101514.heic",
        "title": "Ma crème de chou-fleur",
        "ingredients": [
            "1 chou-fleur, 1 oignon",
            "8 g. d'ail, 4 c. à thé sel",
            "1 boîte de bouillon de bœuf",
            "1 oz, 1 c. à soupe huile",
            "1 patate géante en dés à dais Verde",
            "carrés d'ail, 1 ciboulette champagne",
            "Laver, blanchir le chou-fleur entier",
            "et grosses ail de poêle, faire revenir",
            "l'oignon ail dans la poêle. Renvoyer",
        ],
        "steps": [
            "Laver et blanchir le chou-fleur entier.",
            "Faire revenir oignon et ail.",
            "Ajouter chou-fleur, patate, sel et bouillon.",
            "Mijoter jusqu'à tendre, passer au mélangeur.",
            "Garnir de ciboulette.",
        ],
    },
    # --- page 23 (101521) ---
    {
        "src": "20260503_101521.heic",
        "title": "Soupe à l'arachide de Côte d'Ivoire",
        "ingredients": [
            "1/4 t. de beurre, 1 gros oignon en dés, 2 branches",
            "de céleri haché, 1 c. à soupe de farine",
            "1 t. bouillon de poulet, 1 t. de lait, 1 t. crème",
            "arachide croquant, 1 c. à thé sel de céleri",
            "1 c. à soupe sel, 1 c. à soupe de jus de citron",
            "Fondre beurre, revenir oignon et céleri",
            "5 min ou bien, ajouter farine,",
            "ajouter bouillon, crème, 30 min,",
            "filtrer du bouillon 10 min ou en se rendant",
            "de céleri, ajouter une crème de",
            "arachide jusqu'à ce que une mélange,",
            "homogène, ajouter sel et",
            "couvrir et cuire à feu doux 30 min, sel, poivre.",
        ],
        "steps": [
            "Fondre le beurre, faire revenir l'oignon et le céleri 5 min.",
            "Saupoudrer de farine, ajouter bouillon, lait et crème.",
            "Ajouter beurre d'arachide croquant et sel de céleri.",
            "Mijoter 30 min en remuant pour homogénéiser.",
            "Saler, poivrer, ajouter jus de citron au goût.",
        ],
    },
    {
        "src": "20260503_101521.heic",
        "title": "Soupe œuf et nouilles",
        "ingredients": [
            "1 c. à soupe de beurre, 1 c. à soupe d'huile",
            "vert, 4 c. à soupe Tabasco, c'est doré",
            "4 oz d'huile, 3 c. à soupe gomme et sel",
            "4 t. bouillon de poulet, 3 g. petits beurre",
        ],
        "steps": [
            "Faire fondre le beurre dans une casserole.",
            "Ajouter ail et oignon, faire dorer.",
            "Ajouter le bouillon de poulet, porter à ébullition.",
            "Verser un œuf battu en filet, ajouter les nouilles fines, cuire 3 min.",
        ],
    },
    # --- page 24 (101529) ---
    {
        "src": "20260503_101529.heic",
        "title": "Crème de brocoli (carottes en dés)",
        "ingredients": [
            "Carotte en dés 1 1/2 c. à thé d'huile d'oignon",
            "5 branches d'oignon vert mince",
            "1 1/2 c. à thé farine, 1 c. à thé curry, son",
            "120 g, 35 t. ou plus, 1 c. à thé sel ou",
            "5 t. d'épinards en cubes",
            "Chauffer l'huile et beurre dans casserole",
            "ajouter oignon, mijoter 5 min, ajouter",
            "farine, curry, sel et poivre, mijoter, ajouter brocoli, mijoter",
            "5 min, ajouter sel, ajouter le filet, mijoter 1 oz",
            "lait au four, et 1 c. à thé sel et poivre",
            "10 min, baisser le feu, ajouter crème ramolli, ajouter dans le bol",
            "soupe est sur, mais sans ramolli, ajuster, sel, poivre, ajouter une crème, soupe avec des croûtons, ajouter le vrai épinards",
        ],
        "steps": [
            "Chauffer l'huile et le beurre, faire revenir oignon 5 min.",
            "Ajouter farine, curry, sel et poivre.",
            "Ajouter brocoli, mijoter 5 min.",
            "Ajouter le lait, mijoter 10 min.",
            "Ajouter crème, ajuster sel et poivre, servir avec croûtons.",
        ],
    },
    {
        "src": "20260503_101529.heic",
        "title": "Crème de cheddar",
        "ingredients": [
            "Brocoli, 4 t. d'eau ou 5 fleurs",
            "1 oignon, 1 céleri, 1 cheddar en dés (1)",
            "1 c. à soupe beurre, 2 t. lait 3 1/2 t.",
            "Beurre, 4 c. à soupe de farine",
            "4 c. à soupe d'huile, 1 oignon en dés, sel, poivre",
            "céleri en cubes, 3 c. à thé pâte",
            "ajouter beurre, base 2 min,",
            "1 boîte de céleri à thé eau pour soupe.",
        ],
        "steps": [
            "Cuire brocoli à l'eau jusqu'à tendre.",
            "Faire fondre beurre, faire revenir oignon et céleri en dés.",
            "Ajouter farine, faire un roux, mouiller avec le lait.",
            "Ajouter le brocoli, le cheddar, mijoter.",
            "Saler, poivrer, servir.",
        ],
    },
    # --- page 25 (101536) ---
    {
        "src": "20260503_101536.heic",
        "title": "Sauce crème de Cali",
        "ingredients": [
            "1 c. à soupe huile d'olive",
            "1 céleri, 1 oignon haché, 1 cardon",
            "céleri, 1 g. d'ail mince en cubes",
            "1 c. à soupe d'huile, 1 t. d'olives",
            "(des palourdes), 1 c. à thé sel, 1 t. à thé poivre",
            "5 lait, 1 c. à thé thym, 1 t. patate en",
            "1/2 c. à thé chili en poudre, 1 1/2 t. de",
            "bouillon poulet, 1 t. soupe Pesto, 3 t.",
            "1/2 t. fromage à la crème, 1 t. froide",
            "10 min, ajouter liquides, ajouter crème, ajouter",
            "1 t. tomate 15%",
        ],
        "steps": [
            "Faire revenir oignon, céleri, ail dans l'huile.",
            "Ajouter patate, thym, chili et liquides (bouillon, lait).",
            "Mijoter 10 min jusqu'à tendre.",
            "Ajouter pesto, fromage à la crème, mijoter pour incorporer.",
            "Ajouter les tomates, saler et poivrer.",
        ],
    },
    {
        "src": "20260503_101536.heic",
        "title": "Soupe-crème de chou-fleur (gros chou-fleur)",
        "ingredients": [
            "Hôtel d'Henri Brand California",
            "3 t. d'eau, 2 t. chou-fleur en dés (gros)",
            "1 carotte tranchée, 1 c. à soupe pâte d'ail",
            "1 c. à thé bouillon de poulet, 1 oignon",
            "1 céleri, 1 cube en bouillon, beurre",
            "sel, poivre blanc",
            "1 c. à soupe pâte de tomate, 1 t. de pâte",
            "Fondre beurre, ajouter oignon, paprika doux,",
            "10 min, fermer le rond, et garder tomate ou pâte de tomate, sel et fines herbes au goût",
            "servir.",
        ],
        "steps": [
            "Cuire chou-fleur, carotte et oignon dans bouillon.",
            "Ajouter pâte d'ail et céleri.",
            "Faire fondre beurre, faire revenir paprika 10 min.",
            "Ajouter pâte de tomate, sel et fines herbes au goût.",
            "Servir.",
        ],
    },
    # --- page 26 (101549) ---
    {
        "src": "20260503_101549.heic",
        "title": "Soupe légumes Marocaine",
        "ingredients": [
            "1 carotte en cubes, 1/2 oignon, 1 branche de",
            "céleri, 1 patate moyenne en dés, 2 c. à soupe",
            "de tomates, 1/2 c. à thé de marjolaine",
            "1 sachet soupe oignon style Lipton goût",
            "moutarde, leur de mer, sel, poivre",
            "1 sl en pluie",
            "Ajouter la solution d'eau, ajouter le bouillon",
            "légumes assaisonnés. Mais quand le",
            "10 min ajouter jus tomate et",
            "soupe Lipton, sel, poivre, mijoter",
        ],
        "steps": [
            "Faire revenir carotte, oignon, céleri.",
            "Ajouter patate, tomates et marjolaine.",
            "Ajouter eau et bouillon, mijoter 10 min.",
            "Ajouter jus de tomate et soupe oignon Lipton, mijoter encore 5 min.",
            "Saler, poivrer.",
        ],
    },
    {
        "src": "20260503_101549.heic",
        "title": "Crème de poireaux S.P.",
        "ingredients": [
            "2 pommes de terre coupées en cubes",
            "1 patate ou pomme hachée, 1 g. d'ail fin",
            "1 poireau émincé, 5 t. bouillon",
            "de poulet, 1/2 t. crème de cuisson",
            "1 g de laurier, un peu de thym",
            "Cuire oignon, ail, pomme de terre,",
            "les poireaux, le poireau, 5 min,",
            "ajouter bouillon, laurier et thym",
            "Mijoter 30 min, retirer feuille de",
            "laurier, passer au blender,",
            "réduire en purée, ajouter la crème, sel, poivre.",
        ],
        "steps": [
            "Faire revenir oignon, ail et poireau émincé 5 min.",
            "Ajouter pommes de terre, bouillon, laurier et thym.",
            "Mijoter 30 min jusqu'à tendre.",
            "Retirer la feuille de laurier, passer au blender.",
            "Ajouter la crème, saler, poivrer.",
        ],
    },
    # --- page 27 (101556) ---
    {
        "src": "20260503_101556.heic",
        "title": "Clam Chowder Boston (4 personnes)",
        "ingredients": [
            "60 g de lardons en dés (bacon)",
            "1 oignon haché, 1 branche de céleri",
            "haché, 1 g. d'ail, 1 t. de farine",
            "1 1/2 t. de palourdes, 4 t. de bouillon",
            "Réserve l'ail, jus de palourdes",
            "qu'à 1 oz, ajouter farine, mijoter",
            "ajouter palourdes, crème, jaunes",
            "Cuire à feu doux, ajouter le sel et",
            "feuille de laurier jusqu'à tendre",
            "Avec la crème, ajouter 20 min de cuisson",
            "Réduire et la 3 boîte de soupe",
            "Verser pour réfléchir et separer",
            "Lampe avec une ou ajouter le sel",
            "qui préparation de jaune œuf cuit",
            "Soulèvent par moyen, jusqu'à",
            "+ palourdes, lâche, ajouter ou deux",
            "atomatiquement de croûtons ou",
            "de pain",
        ],
        "steps": [
            "Faire revenir les lardons, l'oignon, le céleri et l'ail.",
            "Ajouter la farine, mijoter, faire un roux.",
            "Ajouter les palourdes, le bouillon et la crème.",
            "Cuire à feu doux avec laurier jusqu'à tendre.",
            "Réduire (passer au mélangeur), ajouter sel et poivre.",
            "Servir avec croûtons ou morceaux de pain.",
        ],
    },
    # --- page 28 (101836) ---
    {
        "src": "20260503_101836.heic",
        "title": "Soupe poulet et nouilles (rapide)",
        "ingredients": [
            "1 carcasse de poulet entier",
            "1 c. à soupe huile, 1 c. à soupe huile, 1 c. à soupe sel",
            "carcasse, 1 oignon, 2 g. d'ail, 1 c. à soupe sel, 1/2 c. à thé poivre",
            "6 t. de bouillon de poulet, 1 c. à soupe pâte de Vermicelle",
            "ou 6 g. de pâte alimentaire, un peu de sel",
            "fondu",
        ],
        "steps": [
            "Mettre carcasse de poulet, oignon, ail, sel et poivre dans casserole.",
            "Couvrir d'eau, faire bouillir, écumer.",
            "Mijoter 1 h, retirer la carcasse, désosser.",
            "Remettre poulet et bouillon, ajouter vermicelle ou pâte alimentaire, cuire jusqu'à tendre.",
        ],
    },
    {
        "src": "20260503_101836.heic",
        "title": "Soupe tomate orge",
        "ingredients": [
            "1 oignon, 5 lt eau, 1 cube",
            "bouillon, 3 carottes en dés, 1 céleri,",
            "1 zucchini en dés, 1 c. à thé sel, 1 navet",
            "environ 1 kg de viande de poulet",
            "cuit en dés, 1/2 t. orge perlé",
            "2 c. à soupe de fenouil, 2 c. à soupe huile",
            "1.5 litres bouillon de poulet, basilic",
            "Mijoter, fenouil, basilic",
            "Cuire avec orge.",
        ],
        "steps": [
            "Faire revenir l'oignon dans l'huile.",
            "Ajouter eau, bouillon, légumes, sel.",
            "Ajouter le poulet en dés, l'orge perlé, fenouil et basilic.",
            "Mijoter jusqu'à ce que l'orge soit cuit.",
        ],
    },
    {
        "src": "20260503_101836.heic",
        "title": "Soupe orge et lentilles",
        "ingredients": [
            "Cuire l'orge 25 min",
            "1 t. bouillon de poulet, 2 g. d'ail fin",
            "1 c. à thé oignon en poudre, 4 grosses carottes",
            "hachées avant cuisson, 1/2 t. lentilles",
            "(seules), 1/2 t. orge non cuit",
        ],
        "steps": [
            "Cuire l'orge 25 min.",
            "Ajouter bouillon, ail, oignon en poudre et carottes.",
            "Ajouter lentilles, mijoter jusqu'à tendres.",
            "Saler, poivrer et servir.",
        ],
    },
    # --- page 29 (101856) ---
    {
        "src": "20260503_101856.heic",
        "title": "Soupe tomate à orge",
        "ingredients": [
            "1 oignon, 1 boîte tomates 28 oz, 4 t.",
            "d'eau, 1 cube bouillon, 1 t. à soupe basilic",
            "1 c. à thé thym, 1 c. à thé persil",
            "Ajouter à l'huile, 1 oignon en cubes,",
            "5 min de huile, ajouter chair, hachons",
            "Tomate en sel, ébullition, ajouter",
            "mijoter 20 min, fond, ajouter Tomate en mélangeur, mijoter 30 min.",
            "Chauffer ajouter orge assaisonné, sel, poivre, oignons.",
        ],
        "steps": [
            "Faire revenir l'oignon dans l'huile 5 min.",
            "Ajouter tomates, eau, bouillon, basilic, thym et persil.",
            "Mijoter 30 min, ajouter l'orge.",
            "Cuire jusqu'à ce que l'orge soit tendre.",
            "Saler, poivrer.",
        ],
    },
    {
        "src": "20260503_101856.heic",
        "title": "Soupe courge-carotte",
        "ingredients": [
            "2 c. à soupe beurre, 2 échalotes, 1 oignon",
            "(coupé ou oignon), 2 c. à soupe sel, 1",
            "1 pomme de terre en dés, 2 carottes",
            "2 c. à soupe courge butternut en dés",
            "ferme en dés, palette de poulet, sel, poivre",
            "4 t. de bouillon de poulet, 1 c. à soupe de",
            "Revenir dans l'huile pour mijoter,",
            "à partir, faire revenir l'oignon, mijoter pour",
            "couvert 30 min, blender, sel, poivre",
        ],
        "steps": [
            "Faire revenir oignon et échalotes dans le beurre.",
            "Ajouter pomme de terre, carottes et courge en dés.",
            "Mouiller avec le bouillon de poulet.",
            "Mijoter à couvert 30 min, passer au blender.",
            "Saler, poivrer.",
        ],
    },
    {
        "src": "20260503_101856.heic",
        "title": "Soupe macaroni",
        "ingredients": [
            "2 t. d'eau, 4 t. bouillon de poulet, 1 lt de",
            "pâte tomate, 1 lb de gros tomates, 1 lb",
            "tomate en dés, 1 oignon, 1/2 t. patate alimentaire (alphabet ou autre), sel, poivre",
            "basilic",
        ],
        "steps": [
            "Mettre eau, bouillon, pâte de tomate, tomates et oignon dans casserole.",
            "Mijoter 30 min, ajouter pâte alimentaire (alphabet ou macaroni).",
            "Cuire jusqu'à tendre, saler, poivrer.",
            "Ajouter basilic.",
        ],
    },
    # --- page 30 (101912) ---
    {
        "src": "20260503_101912.heic",
        "title": "Potage pomme et oignon",
        "ingredients": [
            "1 c. à 6, 1/2 oignon",
            "2 c. à soupe granola, 2 pommes Granny",
            "soupe de céleri, 4 t. bouillon poulet",
            "2 c. à soupe sirop d'érable, 1/4 t. crème 35%",
            "sel, poivre, sherry",
            "Revenir l'oignon mince, ajouter les",
            "à soupe de Granny, soupe céleri 5 min, 2 à 3 min",
            "ajouter bouillon, soupe ginger, cuire 30 min,",
            "Réservé et mettre au mélangeur,",
            "ajouter la crème et sirop d'érable, comme",
            "Pour avoir un cuisinier de poireau, à goûts",
            "caraméliser, le Sherry et un croûton",
            "ou cheddar fort doré.",
        ],
        "steps": [
            "Faire revenir l'oignon mince, ajouter les pommes Granny et le céleri 5 min.",
            "Ajouter bouillon de poulet et gingembre, cuire 30 min.",
            "Passer au mélangeur, ajouter crème et sirop d'érable.",
            "Garnir de Sherry et de croûtons au cheddar fort doré.",
        ],
    },
    {
        "src": "20260503_101912.heic",
        "title": "Soupe poulet et gnocchi de pomme de terre (4 pers.)",
        "ingredients": [
            "1 lb. poitrines de poulet cuites effilochées",
            "1 c. à soupe beurre, 3 c. à soupe à l",
            "1/4 t. farine, 1 paquet ou pâte 4 c. à soupe",
            "soupe d'ail fin, 6 t. bouillon poulet",
            "3 t. lait, 1 t. carottes râpées, 2 c. à thé",
            "feuille fine, sel, poivre, 1 lb de soupe en",
            "morceaux de pomme de terre, 1 t. d'épinards",
            "frais",
            "Dans un grand chaudron, fondre beurre",
            "huile, ajouter oignon, carotte, ail",
            "et cuire jusqu'à oignon transparent",
            "ajouter ferme à poulet (1 min)",
        ],
        "steps": [
            "Dans un grand chaudron, fondre le beurre, ajouter oignon, carotte et ail.",
            "Cuire jusqu'à oignon transparent.",
            "Saupoudrer de farine, ajouter bouillon et lait.",
            "Ajouter le poulet effiloché et les épinards.",
            "Ajouter les gnocchi de pomme de terre, cuire jusqu'à ce qu'ils flottent.",
            "Saler, poivrer.",
        ],
    },
    # --- page 31 (101925) ---
    {
        "src": "20260503_101925.heic",
        "title": "Soupe pois cassé comme au montréal",
        "ingredients": [
            "1 t. de pois cassé, 4 à 6 t. de",
            "bouillon de gibier, 1 t. d'oignon en dés",
            "3 g. d'ail fin, 1 jambon en dés, 1 c. à thé pâte",
            "tomate, 2 c. à thé d'orge en cubes, 1 c. à soupe",
            "thym frais, sel, poivre, sucre suis",
            "à le mais cuit, ajouter du mais (poids",
            "sucré ou maïs en grain)",
        ],
        "steps": [
            "Mettre pois cassé, bouillon, oignon, ail et jambon dans casserole.",
            "Ajouter pâte de tomate, orge, thym, sel et poivre.",
            "Mijoter 1 h 30, ajuster avec eau si trop épais.",
            "Ajouter mais sucré en fin de cuisson.",
        ],
    },
    {
        "src": "20260503_101925.heic",
        "title": "Soupe de betterave et persil",
        "ingredients": [
            "1 lb betteraves pelées coupées en cubes",
            "oignon, 250 g de légumes, 2 carottes",
            "céleri pelées, 2 g. d'ail, 1 oignon",
            "marjolaine ou persil, 1 c. à thé vinaigre",
            "blanc, 1 c. à thé sel, 1 c. à thé de",
            "poivre",
        ],
        "steps": [
            "Mettre betteraves, oignon, carottes, céleri et ail dans une marmite.",
            "Ajouter eau pour couvrir, mijoter jusqu'à tendre.",
            "Ajouter vinaigre blanc, sel et poivre.",
            "Garnir de marjolaine ou persil avant de servir.",
        ],
    },
    {
        "src": "20260503_101925.heic",
        "title": "Soupe du Cameroun",
        "ingredients": [
            "1 poulet désossé en morceaux, 1 oignon",
            "3 g. d'ail, 1 tomate, jus d'un citron, sel",
            "(continue sur page suivante)",
        ],
        "steps": [
            "Faire revenir poulet, oignon, ail et tomate.",
            "Mouiller, ajouter jus de citron, sel.",
            "Mijoter jusqu'à ce que le poulet soit tendre.",
        ],
    },
    # --- page 32 (101950) ---
    {
        "src": "20260503_101950.heic",
        "title": "Soupe du pêcheur Côte d'Ivoire",
        "ingredients": [
            "200 g de poisson, 500 g de fruits de mer",
            "(crabe, crevettes, ou sac de fruits de",
            "mer pré-coupés), 4 tomates, 3 aubergines",
            "(menthi), 75 ml huile, 1 litre d'eau",
            "4 oignons, 1 piment rouge, riz blanc",
            "Cuire 45 min",
            "1 c. à thé gingembre en poudre ou frais",
            "6 c. à soupe beurre arachide, 1 piment",
            "au choix, on peut ajouter du riz",
        ],
        "steps": [
            "Mettre poisson, fruits de mer, tomates et aubergines dans une marmite.",
            "Ajouter huile, eau, oignons, piment, gingembre.",
            "Mijoter 45 min.",
            "Ajouter beurre d'arachide en fin de cuisson.",
            "Servir avec riz blanc.",
        ],
    },
    {
        "src": "20260503_101950.heic",
        "title": "Soupe italienne (boulettes de viande)",
        "ingredients": [
            "Boulettes de viande:",
            "1/2 lb. bœuf haché, 1/2 lb. veau haché",
            "1 œuf battu, 1/2 t. chapelure italienne",
            "1/4 t. fromage Romano râpé, sel, poivre",
            "Soupe: 1/2 lb bœuf avec os, 1/3 lb",
            "poulet avec os, 1 t. carottes en dés",
            "1 t. oignon en dés, 3/4 t. céleri en dés",
            "1 c. à soupe sel fin, 3/4 t. pâtes",
            "grain de blé non cuites, sel, poivre",
        ],
        "steps": [
            "Préparer les boulettes en mélangeant viande, œuf, chapelure, fromage, sel et poivre.",
            "Cuire bœuf et poulet avec os dans l'eau pour faire le bouillon.",
            "Ajouter légumes en dés et boulettes, mijoter 1 h.",
            "Ajouter pâtes 15 min avant la fin.",
        ],
    },
    {
        "src": "20260503_101950.heic",
        "title": "Soupe Jamaicaine au bœuf",
        "ingredients": [
            "4 litres d'eau, 6 courtillons en dés (chayote)",
            "2 chayotes en dés et pelés, 1 oz de",
            "Vermicelle, 1 1/2 lb. bœuf à bouillon",
            "3 à 4 minutes en dés, 1 g. d'ail fin haché",
            "thym frais, sel, poivre",
        ],
        "steps": [
            "Mettre eau, bœuf et chayotes dans une grande marmite.",
            "Ajouter ail et thym, mijoter 3 à 4 min.",
            "Cuire jusqu'à tendre, ajouter vermicelle vers la fin.",
            "Saler, poivrer.",
        ],
    },
    # --- page 33 (101958) ---
    {
        "src": "20260503_101958.heic",
        "title": "Soupe au pois canadienne",
        "ingredients": [
            "3 t. de pois cassés, 1 cube de bouillon",
            "de poulet, 3 t. eau (eau d'un mais)",
            "lardon en dés, oignon en dés, 1 t. de",
            "lardon en dés, jambon de cabri, 1 jambon",
            "de Sannivel, 1 feuille de laurier, sel, poivre",
        ],
        "steps": [
            "Faire tremper les pois cassés.",
            "Mettre dans une marmite avec eau, bouillon, lardon et oignon.",
            "Ajouter le jambon, le laurier, sel et poivre.",
            "Mijoter 2 à 3 h jusqu'à ce que les pois soient bien fondus.",
        ],
    },
    {
        "src": "20260503_101958.heic",
        "title": "Soupe Moldave poulet et pâtes",
        "ingredients": [
            "1 petit poulet en morceaux (3 lbs)",
            "12 t. d'eau, 3 c. à thé sel, 1 oignon",
            "1 grosse carotte, 1 c. à soupe pâte de",
            "tomate ou 1 t. tomate plomb, 2 t. de",
            "nouilles cuit, sel, poivre, persil",
            "3 c. à soupe thym, 1/2 t. à thé",
            "1/2 t. persil frais haché",
        ],
        "steps": [
            "Mettre poulet, eau, sel et oignon dans une marmite.",
            "Mijoter jusqu'à tendre.",
            "Ajouter carottes, pâte de tomate, thym.",
            "Ajouter nouilles cuites, persil frais.",
        ],
    },
    {
        "src": "20260503_101958.heic",
        "title": "Soupe Chinoise aigre et épicée",
        "ingredients": [
            "200 g tofu, 100 g jambon ou cendrier",
            "épicé, 200 g pâte de mer, 100 g",
            "champignon, shiitake, l'amidon en bâton",
            "fin",
            "Couper en petit morceau, 10 g de",
            "gingembre fin, 1 échalote, 1 c. à thé",
            "sel, 1 g sel et morue en dés",
            "1 sucre, 1 c. à soupe vinaigre, 2 c. à soupe",
            "sauce diluée dans 2 c. à soupe d'eau froide,",
            "1/2 c. à thé sucre, huile de canola",
            "35 g salzanaque, 60 ml d'eau froide",
        ],
        "steps": [
            "Couper tofu, jambon, fruits de mer et champignons en petits morceaux.",
            "Faire chauffer l'huile, ajouter gingembre, échalote.",
            "Ajouter le bouillon, le tofu, le jambon, les fruits de mer.",
            "Ajouter vinaigre, sucre, sel et sauce diluée à l'amidon.",
            "Mijoter, servir avec coriandre.",
        ],
    },
    # --- page 34 (102010) ---
    {
        "src": "20260503_102010.heic",
        "title": "Soupe Mexicaine Tortilla",
        "ingredients": [
            "3 poitrines de poulet, 1/2 vermicelle",
            "1 g. d'ail, 1 oz, 3 t. bouillon de",
            "poulet avec, 1 t. de café d'huile",
            "fromage râpé, 1 paquet Tortilla",
            "Crème de poire",
        ],
        "steps": [
            "Cuire les poitrines de poulet dans le bouillon, effilocher.",
            "Faire revenir oignon et ail.",
            "Ajouter bouillon, poulet, vermicelle.",
            "Garnir de tortillas, fromage râpé, crème.",
        ],
    },
    {
        "src": "20260503_102010.heic",
        "title": "Soupe Inde de Dal",
        "ingredients": [
            "4.5 t. eau, 1 lentille rouge",
            "1/4 t. haricots rouge, 2 c. à soupe",
            "d'huile, 1 g. d'ail fin, 1 c. à thé thym, 1 c. à",
            "thé cardamome, 1 oignon en cubes, 4 c. à thé",
            "ail fin, 1 oz, 1 1/2 t. tomate",
            "3 oz, 1 c. à thé tomate, 1 c. à thé curry",
            "rouge, 1 c. à thé curry doux, 2 c. à thé garam",
            "masala, 1 1/2 c. à thé poudre de",
            "coriandre, une pincée de",
            "1/4 c. à thé sel, 1 c. à soupe Karam",
            "doré, 2 à 3 c. à thé d'huile, 1 c. à thé sucre",
            "panais rouge, plus le crème de fraîche",
            "1/4 c. à soupe gros sel, 1 pincée de",
        ],
        "steps": [
            "Tremper lentilles et haricots à l'avance, cuire jusqu'à tendre.",
            "Faire revenir oignon, ail, thym, cardamome dans l'huile.",
            "Ajouter tomate, curry, garam masala, coriandre.",
            "Mélanger avec lentilles cuites, mijoter 30 à 40 min.",
            "Ajouter crème fraîche en fin, sel et garam doré.",
        ],
    },
    # --- page 35 (102016) ---
    {
        "src": "20260503_102016.heic",
        "title": "Soupe Mayes (Liens, Vietnamienne)",
        "ingredients": [
            "1 c. à soupe huile d'olive, 500 g",
            "bœuf haché, 2 oignons en dés, 2",
            "branches céleri en dés, 3 g. d'ail fin",
            "fin haché, 1 c. à thé carotte",
            "1 1/2 c. à thé cumin, 1 c. à thé coriandre",
            "1 c. à thé poudre de cayenne, sel",
            "1 c. à thé pâte de tomate, 1/2 c. à thé cardamome",
            "moulu, 1 c. à thé sel, 4 t. tomate",
            "saliés, 4 T bouillon poulet, 1/4 t.",
            "ail, 1 1/2 hachette pour rouge, 4 c. à",
            "thé d'huile, 1/4 t. lentille verte non rincée jus",
            "de lime, sel, poivre",
        ],
        "steps": [
            "Faire revenir bœuf haché, oignons, céleri et ail dans l'huile.",
            "Ajouter cumin, coriandre, cayenne, pâte de tomate et cardamome.",
            "Ajouter tomates et bouillon, mijoter.",
            "Ajouter lentilles vertes, cuire jusqu'à tendres.",
            "Servir avec jus de lime, sel et poivre.",
        ],
    },
    # --- page 36 (102033) ---
    {
        "src": "20260503_102033.heic",
        "title": "Soupe à l'agneau au lieu romain",
        "ingredients": [
            "1 t. de pois chiches, 1 oignon, 1 c. à soupe",
            "huile, 4 morceaux d'agneau, 4 t. bouillon",
            "de bœuf, sel, poivre, jus de tomate",
            "2 lb d'agneau couper(?) en morceaux",
            "(continue)",
        ],
        "steps": [
            "Faire revenir l'agneau dans l'huile.",
            "Ajouter oignon, pois chiches, bouillon de bœuf.",
            "Mijoter jusqu'à ce que la viande soit tendre.",
            "Ajouter jus de tomate, sel, poivre.",
        ],
    },
    {
        "src": "20260503_102033.heic",
        "title": "Soupe orge au saucisson",
        "ingredients": [
            "1 t. de saucisson, 1 t. orge perlé",
            "champignons, 1 t. tomate concassé",
            "Lait, 1 c. à thé d'huile, jambon ou saucisson",
            "1/2 oz, 1 c. à thé d'oignon ou bouillon",
            "soupe d'ail, 1 t. tomate",
            "1 oz, 1 oz, 4 t. de bouillon",
            "(continue)",
        ],
        "steps": [
            "Faire revenir saucisson et oignon.",
            "Ajouter ail, tomate, champignons.",
            "Ajouter bouillon et orge, mijoter jusqu'à tendre.",
            "Saler, poivrer.",
        ],
    },
    # --- page 37 (102043) ---
    {
        "src": "20260503_102043.heic",
        "title": "Soupe au pistou (4 pers.)",
        "ingredients": [
            "1/2 oz pour soupe, 1 - 1.5 c. à soupe",
            "soupe verte, 1 t. à soupe pistou en",
            "dés, 1 oignon soupe en dés, 2 t. à",
            "soupe haricots en lanières, 1 t. de",
            "Tomates, 2 g. ail, 4 t. bouillon de",
            "1 oignon, 1/2 t. de pâte alimentaire petits",
            "1/2 oz pois rouges en cubes, 1 c. à thé sel, poivre",
            "1/4 t. parmesan râpé, 2 t. fenouil tendre",
            "frais, 1 1/2 c. à soupe basilic frais ciselé",
            "Réservé au feu, en bain l'huile d'olive",
            "et l'ail, 5 min, ajouter l'oignon en dés",
            "ferme, 20 min, ajouter le persil et",
            "le pistou, sel, poivre",
        ],
        "steps": [
            "Faire revenir oignon, ail dans l'huile.",
            "Ajouter haricots, tomates, bouillon, mijoter.",
            "Ajouter petits pâtes alimentaires, pois rouges.",
            "Mijoter 20 min, ajouter pistou, persil, sel, poivre.",
            "Servir avec parmesan râpé.",
        ],
    },
    {
        "src": "20260503_102043.heic",
        "title": "Soupe pour le jour traditionnel",
        "ingredients": [
            "6 pers.",
            "2 c. à soupe huile, 1 1/2 t. d'oignon en dés",
            "ou 1 1/2 lb de paleron, 1 carotte",
            "en dés, 1 céleri en dés, 1 chou-fleur",
            "en dés, 1 g. d'ail fin, 6 t. bouillon de",
        ],
        "steps": [
            "Faire revenir oignon dans l'huile.",
            "Ajouter paleron, carotte, céleri, chou-fleur et ail.",
            "Mouiller avec le bouillon, mijoter 1 à 2 h.",
            "Saler, poivrer.",
        ],
    },
    # --- page 38 (102058) ---
    {
        "src": "20260503_102058.heic",
        "title": "Soupe crevettes-fenouil et safran (4 pers.)",
        "ingredients": [
            "1 bulbe de fenouil en lanières, 2 g.",
            "d'ail fin, 1/2 oignon haché, 2 c. à soupe",
            "huile de canola fin, 4 c. à soupe",
            "huile d'olive, 1 pincée tête en dés, 1/2 t.",
            "vin blanc, 1 pincée safran, 2 c. à thé",
            "paprika doux, 1 t. tomates en dés en",
            "conserve, 1 c. à soupe pâte de tomate",
            "4 t. fumet poisson ou bouillon poulet",
            "16 crevettes coupées en 2 dans le sens",
            "2 c. à soupe persil frais ciselé",
            "Faire revenir fenouil, ail, oignon, céleri 5 min dans l'huile",
            "ajouter patate (5 min), safran, paprika doux, à couvert. Mettre",
            "tomates en dés, pâte de tomate, fumet poisson, bouillon poulet",
            "cuire 15 min, ajouter crevettes, persil",
            "cuire 3 min, servir.",
        ],
        "steps": [
            "Dans une casserole, faire revenir fenouil, ail, oignon et céleri 5 min dans l'huile.",
            "Ajouter pomme de terre 5 min, puis safran et paprika.",
            "Couvrir, ajouter tomates, pâte de tomate, fumet de poisson ou bouillon de poulet.",
            "Cuire 15 min.",
            "Ajouter crevettes et persil, cuire 3 min.",
            "Servir.",
        ],
    },
    # --- page 39 (102105) ---
    {
        "src": "20260503_102105.heic",
        "title": "Crème de patate, douce et courge",
        "ingredients": [
            "1 oignon, 4 t. d'eau (4 lt), 1 patate en dés",
            "2 c. à soupe gingembre, 1 c. à soupe sel, 2 c. à",
            "soupe d'huile, 2 1/2 t. patate douce",
            "ferme, 2 c. à thé cumin frais, 1 c. à thé",
            "poudre de cumin, 4 t. bouillon poulet",
            "1/2 t. crème 15%, 1 cube de pâte",
            "Revenir l'oignon, ajouter, gingembre",
            "3 min en remuant, ajouter la patate",
            "douce en cubes, cuire un peu, ajouter",
            "1 c. à soupe miel, ajouter cumin, sel, poivre",
            "mijoter sur la cuisson, retirer ramollir",
            "imperfections, soupe, blender, sel, poivre",
        ],
        "steps": [
            "Faire revenir l'oignon, ajouter le gingembre, cuire 3 min.",
            "Ajouter la patate douce en cubes, cuire un peu.",
            "Ajouter cumin, sel, poivre, miel.",
            "Mouiller avec bouillon, mijoter jusqu'à ramollir.",
            "Passer au blender, ajouter crème, sel, poivre.",
        ],
    },
    {
        "src": "20260503_102105.heic",
        "title": "Soupe au pois chiche",
        "ingredients": [
            "6 à 8 t. d'eau, 1 1/4 t. pois jaunes, sec",
            "1 navet de feuves, 1 1/2 t. lard sale",
            "en lardons, 1 t. carotte en dés, 1 t. d'oignon",
            "en dés, 1/2 t. carotte hachée, 1/2 t.",
            "bouillon poulet, 2 cubes soupe Lipton",
            "soupe trempée, 1 t. de poireau",
            "(continue)",
        ],
        "steps": [
            "Faire tremper les pois chiches.",
            "Mettre eau, pois, lard salé en lardons dans une marmite.",
            "Ajouter carottes, oignon, poireau, navet de feuves.",
            "Mijoter 2 à 3 h jusqu'à ce que les pois soient tendres.",
            "Ajouter cubes Lipton, ajuster sel et poivre.",
        ],
    },
    # --- page 40 (102140) — page rotated, low confidence ---
    {
        "src": "20260503_102140.heic",
        "title": "Soupe aux tomates fraîches (page tournée)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Voir source pour ingrédients exacts",
        ],
        "steps": [
            "Voir l'image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    {
        "src": "20260503_102140.heic",
        "title": "Soupe au céleri (suite)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
        ],
        "steps": [
            "Voir l'image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 41 (102213) ---
    {
        "src": "20260503_102213.heic",
        "title": "Crème jardinière",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
        ],
        "steps": [
            "Voir l'image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 42 (102227) ---
    {
        "src": "20260503_102227.heic",
        "title": "Soupe au navet (4 pers.)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "1 navet, 1 oignon, 1 c. à soupe huile",
            "céleri, ail, bouillon poulet, sel, poivre",
        ],
        "steps": [
            "Faire revenir oignon dans huile.",
            "Ajouter navet en dés, ail, céleri.",
            "Mouiller avec bouillon, mijoter jusqu'à tendre.",
            "Saler, poivrer.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 43 (102243) ---
    {
        "src": "20260503_102243.heic",
        "title": "Soupe pommes de terre allemande",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Pommes de terre, oignon, lardons",
            "Bouillon, sel, poivre, persil",
        ],
        "steps": [
            "Faire revenir lardons et oignon.",
            "Ajouter pommes de terre, bouillon.",
            "Mijoter jusqu'à tendre, garnir de persil.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 44 (102259) ---
    {
        "src": "20260503_102259.heic",
        "title": "Soupe (page tournée 102259)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
        ],
        "steps": [
            "Voir l'image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 45 (102305) ---
    {
        "src": "20260503_102305.heic",
        "title": "Soupe — recette incomplète (102305)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
        ],
        "steps": [
            "Voir l'image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 46 (102319) ---
    {
        "src": "20260503_102319.heic",
        "title": "Crème de la mer (poireaux et fruits de mer)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Poireaux, fruits de mer, crème, vin blanc",
        ],
        "steps": [
            "Faire revenir poireaux dans le beurre.",
            "Ajouter vin blanc, fumet, crème.",
            "Ajouter fruits de mer, mijoter brièvement.",
            "Saler, poivrer.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 47 (102329) ---
    {
        "src": "20260503_102329.heic",
        "title": "Soupe (page tournée 102329)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
        ],
        "steps": [
            "Voir l'image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 48 (102341) ---
    {
        "src": "20260503_102341.heic",
        "title": "Soupe poulet à mère (recette familiale)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Poulet, oignon, carottes, céleri, riz ou nouilles",
            "Bouillon de poulet, sel, poivre, persil",
        ],
        "steps": [
            "Cuire le poulet dans l'eau pour faire le bouillon.",
            "Ajouter oignon, carottes, céleri.",
            "Mijoter, ajouter riz ou nouilles vers la fin.",
            "Saler, poivrer, garnir de persil.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 49 (102353) ---
    {
        "src": "20260503_102353.heic",
        "title": "Soupe maison à la jardinière",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Légumes variés, bouillon, vermicelle",
        ],
        "steps": [
            "Faire revenir légumes coupés en dés.",
            "Ajouter bouillon, mijoter.",
            "Ajouter vermicelle, cuire jusqu'à tendre.",
            "Saler, poivrer.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 50 (102404) ---
    {
        "src": "20260503_102404.heic",
        "title": "Velouté de la cuvée Italienne",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Tomates, basilic, ail, parmesan, crème",
        ],
        "steps": [
            "Faire revenir ail dans l'huile.",
            "Ajouter tomates, basilic, mijoter.",
            "Passer au mélangeur, ajouter crème.",
            "Servir avec parmesan râpé.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 51 (102502) ---
    {
        "src": "20260503_102502.heic",
        "title": "Crème de poireau et asperges",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Poireau, asperges, pomme de terre, bouillon, crème",
        ],
        "steps": [
            "Faire revenir poireau et asperges.",
            "Ajouter pomme de terre et bouillon, mijoter jusqu'à tendre.",
            "Passer au blender, ajouter crème.",
            "Saler, poivrer.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 52 (102527) ---
    {
        "src": "20260503_102527.heic",
        "title": "Velouté de courge butternut",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Courge butternut, oignon, ail, gingembre, lait de coco",
        ],
        "steps": [
            "Faire revenir oignon, ail, gingembre.",
            "Ajouter courge en dés et bouillon, mijoter jusqu'à tendre.",
            "Passer au blender, ajouter lait de coco.",
            "Saler, poivrer.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 53 (102626) ---
    {
        "src": "20260503_102626.heic",
        "title": "Soupe tomate et orge (variante 2)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Tomates, orge perlé, oignon, céleri, carottes",
            "Bouillon, basilic, sel, poivre",
        ],
        "steps": [
            "Faire revenir oignon, céleri, carottes.",
            "Ajouter tomates et bouillon.",
            "Ajouter orge, mijoter jusqu'à tendre.",
            "Saler, poivrer, garnir de basilic.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 54 (102705) ---
    {
        "src": "20260503_102705.heic",
        "title": "Soupe de pommes de terre crémeuse",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Pommes de terre, poireau, crème, lait, beurre, sel, poivre",
        ],
        "steps": [
            "Faire revenir poireau dans le beurre.",
            "Ajouter pommes de terre et bouillon, mijoter jusqu'à tendre.",
            "Passer au blender, ajouter crème et lait.",
            "Saler, poivrer.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 55 (102712) ---
    {
        "src": "20260503_102712.heic",
        "title": "Soupe Camerounaise (variante)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
            "Légumes africains, bouillon, épices",
        ],
        "steps": [
            "Voir image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile.",
    },
    # --- page 56 (102721) ---
    {
        "src": "20260503_102721.heic",
        "title": "Soupe de fin (délicieux à refaire)",
        "ingredients": [
            "Page photographiée à l'horizontale — transcription incomplète",
        ],
        "steps": [
            "Voir image source pour la recette complète.",
        ],
        "notes_extra": "Page photographiée latéralement, transcription difficile. Annotation: « délicieux à refaire ».",
    },
]


def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    cats = json.loads(CATS_PATH.read_text(encoding="utf-8"))

    # find "les soupes" category
    soupe_cat = next((c for c in cats if c["name"].lower() == "les soupes"), None)
    if soupe_cat is None:
        raise SystemExit("Could not find 'les soupes' category")

    existing_max_id = max(r["id"] for r in recipes)
    next_id = existing_max_id + 1

    # idempotency: skip recipes whose source already appears in any existing notes
    existing_srcs = {
        r.get("notes", "") for r in recipes if r.get("notes")
    }

    added = []
    for entry in NEW_RECIPES:
        src = entry["src"]
        marker = f"BOOK1/{src}"
        if any(marker in n for n in existing_srcs):
            continue
        rid = next_id
        next_id += 1
        notes = VERIFY_NOTE.format(src=src)
        if entry.get("notes_extra"):
            notes = f"{notes}\n{entry['notes_extra']}"
        rec = {
            "id": rid,
            "numberLabel": f"Recette nº {rid}",
            "title": entry["title"],
            "ingredients": entry["ingredients"],
            "steps": entry["steps"],
            "notes": notes,
        }
        recipes.append(rec)
        soupe_cat["recipeIds"].append(rid)
        added.append(rid)

    # write back
    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    CATS_PATH.write_text(
        json.dumps(cats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Added {len(added)} recipes; new IDs: {added[:5]}...{added[-3:] if len(added) > 5 else ''}")
    print(f"Recipes total: {len(recipes)}; les soupes count: {len(soupe_cat['recipeIds'])}")


if __name__ == "__main__":
    main()
