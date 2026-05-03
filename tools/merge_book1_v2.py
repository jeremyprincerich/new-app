"""Phase 3 corrections: replaces the 18 sideways-page recipes (IDs 317-334)
with proper transcriptions produced from the now-upright source photos.

This is a one-shot fix kept here as a re-runnable safety net — if a future
pipeline step ever overwrites recipes 317-334 with the original
"Page photographiée à l'horizontale" stubs, just run this to restore them.

Run from new-app/: `python tools/merge_book1_v2.py`
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes.json"

VERIFY = (
    "Transcrit automatiquement depuis BOOK1/{src}.heic — "
    "à vérifier (titre, quantités et étapes peuvent contenir des erreurs)."
)


SIDEWAYS_REPLACEMENTS = {
    317: ("20260503_102140", "Soupe aux tomates fraîches", [
        "Tomates fraîches (5 ou 6)",
        "1 oignon",
        "huile d'olive",
        "1 patate",
        "1 c. à thé persil",
        "bouillon de poulet",
        "sel, poivre",
    ], [
        "Faire revenir l'oignon dans l'huile d'olive.",
        "Ajouter les tomates fraîches coupées et la patate.",
        "Mouiller avec le bouillon de poulet, mijoter jusqu'à tendreté.",
        "Saler, poivrer, parsemer de persil avant de servir.",
    ]),
    318: ("20260503_102140", "Soupe nouilles aux légumes", [
        "Nouilles fines (2 c. à soupe)",
        "1 céleri",
        "1 oignon",
        "1 carotte",
        "2 patates",
        "Tomate",
        "2 c. à soupe de beurre",
        "1 patate, ciboulette",
    ], [
        "Faire revenir l'oignon, le céleri et la carotte dans le beurre.",
        "Ajouter les patates en dés, la tomate, mouiller au bouillon.",
        "Mijoter jusqu'à tendreté.",
        "Ajouter les nouilles vers la fin, cuire 8 à 10 min.",
        "Saler, poivrer, parsemer de ciboulette.",
    ]),
    319: ("20260503_102213", "Crème à l'oignon caramélisé au navet", [
        "6 oignons émincés",
        "1/4 t. beurre",
        "3 navets blancs en cubes",
        "4 t. bouillon de poulet",
        "1 tasse de lait ou crème",
        "long cuisson de four jusqu'à réduit",
        "sel, poivre",
    ], [
        "Caraméliser les oignons dans le beurre 30 min, les coller au fond pour qu'ils rissolent.",
        "Ajouter les navets en cubes et un peu d'eau pour déglacer.",
        "Ajouter le bouillon, mijoter 30 min.",
        "Mixer, ajouter la crème, sel et poivre.",
        "Réchauffer sans bouillir.",
    ]),
    320: ("20260503_102227", "Soupe poireau et jambon", [
        "3 t. bouillon de poulet",
        "4 patates en cubes",
        "1 céleri haché",
        "1 carotte en dés",
        "1/2 oignon haché",
        "1 jambon (1 lb) en dés",
        "1/2 t. crème",
        "1/2 t. lait",
        "1 c. à soupe farine, sel, poivre",
    ], [
        "Faire revenir l'oignon, la carotte et le céleri.",
        "Ajouter le jambon en dés, brunir 5 min.",
        "Ajouter le bouillon et les patates, mijoter jusqu'à tendreté.",
        "Saupoudrer de farine, ajouter lait et crème.",
        "Saler, poivrer.",
    ]),
    321: ("20260503_102243", "Crème de panais (Hier)", [
        "Panais (3 ou 4)",
        "1 oignon",
        "1 c. à soupe beurre",
        "1 c. à thé thym",
        "bouillon de poulet",
        "lait ou crème 35%",
        "sel, poivre",
    ], [
        "Faire revenir l'oignon dans le beurre.",
        "Ajouter les panais en cubes, le bouillon, le thym.",
        "Mijoter jusqu'à tendreté.",
        "Passer au mélangeur, ajouter le lait/crème.",
        "Saler, poivrer.",
    ]),
    322: ("20260503_102259", "Soupe Annot", [
        "1 oignon",
        "huile d'olive",
        "Tomate (1 boîte)",
        "1 patate",
        "soupe de poulet (cube)",
        "rotini ou autres pâtes",
        "sel, poivre, basilic",
    ], [
        "Faire revenir l'oignon dans l'huile.",
        "Ajouter les tomates et le bouillon.",
        "Mijoter 20 min, ajouter la patate en dés.",
        "Ajouter les pâtes en fin de cuisson, cuire jusqu'à tendre.",
        "Saler, poivrer, ajouter basilic.",
    ]),
    323: ("20260503_102305", "Soupe au Hambourg", [
        "1 lb bœuf haché maigre",
        "2 g d'ail",
        "2 t. de jus de tomate",
        "1 oignon en dés",
        "3 1/2 t. bouillon de bœuf",
        "1 boîte tomates en dés",
        "1 boîte tomate condensée",
        "Tasses de légumes mélangés",
        "1 c. à thé sel, sel d'oignon, sel de céleri",
        "feuille de laurier, basilic",
    ], [
        "Cuire le bœuf haché avec l'oignon et l'ail jusqu'à doré.",
        "Ajouter les tomates et le bouillon.",
        "Ajouter les légumes mélangés et les assaisonnements.",
        "Couvrir et mijoter 1 heure.",
    ]),
    324: ("20260503_102319", "Crème de légumes d'hiver", [
        "3 pommes de terre coupées en morceaux",
        "1 panais en morceaux",
        "1 carotte en morceaux",
        "1 oignon en morceaux, 1 poireau en morceaux",
        "2 c. à soupe de beurre",
        "1 c. à thé thym",
        "4 t. eau chaude",
        "1 cube bouillon",
        "sel, poivre",
        "crème, lait",
    ], [
        "Revenir légumes dans le beurre.",
        "Cuire 10 min, ajouter les assaisonnements.",
        "Ajouter le bouillon chaud et l'eau.",
        "Cuire à découvert environ 30 min.",
        "Réduire en purée, ajouter crème ou lait.",
        "Saler, poivrer.",
    ]),
    325: ("20260503_102329", "Soupe constante au légumes pour soupe", [
        "1 c. à soupe huile d'olive",
        "1 oignon en dés",
        "3 à 5 poireaux émincés",
        "1 boîte tomates V8",
        "1 cube bouillon de poulet",
        "1 c. à soupe d'épices à soupe",
        "8 t. eau",
        "1 c. à soupe sel",
    ], [
        "Faire revenir l'oignon et les poireaux dans l'huile.",
        "Ajouter les tomates V8, le bouillon, l'eau et les épices.",
        "Mijoter 6 à 15 min.",
        "Saler, poivrer.",
    ]),
    326: ("20260503_102341", "Soupe repas nourrissante au poulet", [
        "2 poitrines de poulet",
        "1 c. à soupe d'huile",
        "1 oignon haché, 1 ail haché",
        "1 t. céleri haché",
        "fines herbes (thym, persil)",
        "5 à 6 carottes en rondelles",
        "1 cube bouillon, 5 t. eau",
        "1 c. à thé sel, 100 g vermicelles ou pâtes",
        "10 g de feuilles de coriandre",
    ], [
        "Faire revenir l'oignon, l'ail et le céleri dans l'huile.",
        "Ajouter le poulet coupé en dés et les carottes.",
        "Mouiller avec l'eau et le bouillon.",
        "Ajouter les fines herbes, mijoter 30 min.",
        "Ajouter les vermicelles, cuire 10 min de plus.",
        "Garnir de coriandre.",
    ]),
    327: ("20260503_102353", "Soupe les pois de Hide", [
        "1 c. à thé beurre",
        "1 oignon, 2 carottes",
        "1 t. d'eau, 2 patates pelées en dés",
        "Tomate en dés",
        "1 c. à thé bouillon de poulet",
        "Tasse de haricots blancs",
        "petits pois congelés",
        "sel, poivre",
    ], [
        "Faire revenir l'oignon dans le beurre.",
        "Ajouter carottes, patates, tomates.",
        "Mouiller avec l'eau et le bouillon.",
        "Mijoter 30 min jusqu'à tendreté.",
        "Ajouter haricots blancs et petits pois.",
        "Cuire 15 min de plus, saler, poivrer.",
    ]),
    328: ("20260503_102404", "Velouté de légumes Sibu", [
        "2 c. à soupe huile d'olive",
        "1 carotte en dés",
        "1 céleri en dés",
        "1 oignon",
        "4 t. bouillon de poulet",
        "1 c. à thé curry",
        "1/2 t. lait de coco",
        "1 c. à soupe persil",
        "sel, poivre",
    ], [
        "Faire revenir oignon, carotte et céleri 10 min en remuant souvent.",
        "Ajouter le bouillon et le curry.",
        "Mijoter 15 min.",
        "Passer au mélangeur.",
        "Ajouter le lait de coco, le persil, sel et poivre.",
        "Réchauffer à feu doux.",
    ]),
    329: ("20260503_102502", "Velouté de crème au poireau", [
        "1/4 t. beurre",
        "3 c. à thé farine",
        "1 oignon, 1 poireau",
        "1/2 t. lait, 4 t. bouillon",
        "Tasse pommes de terre en dés",
        "1 c. à thé sel, poivre",
        "1 c. à soupe ciboulette",
        "1/4 t. crème 35%",
    ], [
        "Faire fondre le beurre, faire revenir oignon et poireau.",
        "Ajouter pommes de terre en dés, le bouillon.",
        "Mijoter 15 min jusqu'à tendreté.",
        "Mixer, ajouter la crème, sel, poivre.",
        "Garnir de ciboulette.",
    ]),
    330: ("20260503_102527", "Potage aux carottes au coco", [
        "4 t. bouillon de poulet",
        "1 feuille de laurier",
        "Carottes (3 t.) coupées en rondelles",
        "1 c. à thé curry",
        "1/2 t. lait de coco (15%)",
        "1 c. à thé d'huile",
        "sel, poivre",
    ], [
        "Faire revenir les carottes dans l'huile.",
        "Ajouter bouillon et laurier, mijoter 30 min jusqu'à tendreté.",
        "Mixer, ajouter le curry et le lait de coco.",
        "Saler, poivrer, réchauffer sans bouillir.",
    ]),
    331: ("20260503_102626", "Soupe tomate et orge à mijoter", [
        "1 boîte 28 oz tomate en dés",
        "6 t. bouillon de poulet",
        "1/2 t. orge en cubes",
        "1/2 t. carottes en cubes",
        "1 c. à soupe huile",
        "céleri, oignon",
        "fines herbes (basilic, persil)",
    ], [
        "Faire revenir l'oignon et le céleri dans l'huile.",
        "Ajouter les tomates et le bouillon.",
        "Ajouter l'orge et les carottes.",
        "Mijoter 1 heure jusqu'à orge cuit.",
        "Saler, poivrer, ajouter fines herbes.",
    ]),
    332: ("20260503_102705", "Soupe de fenouil", [
        "1 c. à soupe d'huile d'olive",
        "1 oignon haché",
        "1 fenouil émincé",
        "Tomates en dés en conserve",
        "1 t. bouillon de poulet",
        "Vermicelle",
        "1 t. tomates en dés, 1 t. épinard frais",
        "sel, poivre",
    ], [
        "Faire revenir l'oignon et le fenouil dans l'huile.",
        "Ajouter les tomates et le bouillon.",
        "Mijoter 20 min.",
        "Ajouter le vermicelle, cuire jusqu'à tendre.",
        "Ajouter les épinards frais en fin de cuisson.",
        "Saler, poivrer.",
    ]),
    333: ("20260503_102712", "Chaudrée de fruits de mer", [
        "1 c. à soupe d'huile, 2 branches de céleri en dés",
        "1 oignon haché",
        "1 paquet de fruits de mer (cocktail) congelé",
        "1 boîte de palourdes avec leur jus",
        "1 c. à soupe Vermouth blanc, 1/2 t. crème 35%",
        "1 lb homard, 1 grosse crevette",
        "1 patate en dés, 1 c. à thé sel",
        "5 min cuisson, fenouil",
    ], [
        "Faire revenir oignon et céleri dans l'huile.",
        "Ajouter le vermouth blanc, déglacer.",
        "Ajouter le bouillon, les patates en dés, mijoter 15 min.",
        "Ajouter les fruits de mer congelés, cuire 5 min.",
        "Ajouter la crème, saler.",
        "Servir bien chaud.",
    ]),
    334: ("20260503_102721", "Soupe de Maïs", [
        "1/2 oignon haché",
        "2 branches de céleri",
        "1 c. à soupe de beurre, 3 g. d'ail fin",
        "Carottes (1/4 c. à thé sucre)",
        "3 t. de grains de maïs frais ou congelés",
        "1 grosse patate en dés",
        "3 t. de bouillon de poulet",
        "1/2 t. crème 35%",
        "sel, poivre, ciboulette",
    ], [
        "Faire revenir l'oignon, le céleri et l'ail dans le beurre.",
        "Ajouter le maïs et la patate, mijoter quelques minutes.",
        "Mouiller avec le bouillon, cuire à feu moyen 15 à 20 min.",
        "Mixer en partie pour épaissir, garder des morceaux entiers.",
        "Ajouter la crème, sel, poivre.",
        "Garnir de ciboulette pour servir.",
    ]),
}


def main():
    recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in recipes}
    n_replaced = 0
    for rid, (src, title, ings, steps) in SIDEWAYS_REPLACEMENTS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        rec["title"] = title
        rec["ingredients"] = ings
        rec["steps"] = steps
        rec["notes"] = VERIFY.format(src=src)
        n_replaced += 1
    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Replaced {n_replaced} sideways recipes (IDs 317-334).")


if __name__ == "__main__":
    main()
