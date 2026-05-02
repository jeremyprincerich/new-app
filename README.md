# Cahier de Recettes

Recettes de famille, transmises avec amour — un cahier statique de 236 recettes en français, organisées en 10 catégories.

## Aperçu

- `index.html` — page d'accueil avec présentation
- `cookbook.html` — l'application principale (catégories, fiches recettes, recherche)
- `recipes.json` — données des 236 recettes
- `categories.json` — 10 catégories avec listes de recettes
- `assets/styles.css` — feuille de style
- `assets/app.js` — application vanilla JS (routage par hash)

## Lancer en local

Servez le dossier avec n'importe quel serveur HTTP statique :

```sh
python3 -m http.server 8000
# puis ouvrir http://localhost:8000/
```

## Déploiement

Fonctionne tel quel sur GitHub Pages, Netlify, Vercel ou tout hébergeur statique. Aucune étape de build n'est requise.

## Crédits

Reconstruction d'une application Replit créée à l'origine pour partager les recettes manuscrites de la famille.
