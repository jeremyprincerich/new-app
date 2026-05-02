# Cahier de Recettes

Recettes de famille, transmises avec amour — un cahier statique de **236 recettes** en français, organisées en 10 chapitres.

Aucune étape de build, aucune dépendance. Du HTML, du CSS et un fichier JS de routage à 504 lignes.

## Structure

```
.
├── index.html         # page d'accueil (couverture du livre)
├── cookbook.html      # entrée vers la table des matières
├── assets/
│   ├── app.js         # SPA vanilla : routage par hash (#/sommaire, #/categorie/:slug, ...)
│   └── styles.css     # design d'origine (Playfair Display + Lora + Inter)
├── recipes.json       # 236 recettes (titre, ingrédients, étapes, notes)
├── categories.json    # 10 catégories
├── favicon.svg
├── vercel.json        # cleanUrls + headers (cache, sécurité)
└── package.json       # scripts dev/start
```

## Routes (hash)

| Hash | Vue |
| --- | --- |
| `#/` | Couverture du livre |
| `#/sommaire` | Table des Matières |
| `#/categorie/:slug` | Page d'une catégorie |
| `#/recette/:id` | Fiche recette (Ingrédients · Préparation · Note) |
| `#/recherche` | Recherche par titre ou ingrédient |

## Lancer en local

```sh
npm start          # ou : python3 -m http.server 8765
```

Puis ouvrez http://localhost:8765/.

## Déployer

### Vercel

1. Importez le dépôt sur https://vercel.com/new
2. Framework Preset : **Other** (détecté automatiquement)
3. Build Command et Output Directory : **(laisser vides)**
4. Cliquez **Deploy**

`vercel.json` active déjà les *clean URLs* (sans `.html`) et ajoute les bons en-têtes de cache et de sécurité.

### GitHub Pages

Allez dans `Settings → Pages`, choisissez **main / (root)**, sauvegardez. Le site sera servi à `https://<user>.github.io/new-app/`.

### Netlify, Cloudflare Pages, etc.

Glissez-déposez le dossier — aucun build n'est nécessaire.
