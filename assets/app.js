// Cahier de Recettes — vanilla SPA matching the Replit React version.
// Routes (hash-based for static hosting):
//   #/                     -> hero / book cover
//   #/sommaire             -> Table des Matières (all categories + recipes)
//   #/categorie/:slug      -> Category landing
//   #/recette/:id          -> Recipe detail
//   #/recherche            -> Search
//
// This file is loaded as an ES module (see <script type="module"> in
// cookbook.html / index.html). The IIFE wrapper is preserved for parity with
// the previous structure, but module-scope imports above it provide auth
// helpers from assets/auth.js.

import {
  isConfigured as isAuthConfigured,
  onSessionChange as onAuthChange,
  signOut as authSignOut,
} from "./auth.js";

(function () {
  "use strict";

  // ---------- helpers ----------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]),
    );
  }

  function slugify(s) {
    return String(s)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/&/g, " et ")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function stripEmoji(s) {
    if (!s) return "";
    return String(s)
      .replace(/[\u{1F300}-\u{1FAFF}]/gu, "")
      .replace(/💡\s*/g, "")
      .trim();
  }

  function pad3(n) {
    return String(n).padStart(3, "0");
  }

  function toggleSet(set, value) {
    if (set.has(value)) set.delete(value);
    else set.add(value);
  }

  // Format minutes (number) into French short form: 25 -> "25 min", 90 -> "1 h 30",
  // 60 -> "1 h", 75 -> "1 h 15". Returns null for non-numbers.
  function formatMinutes(n) {
    if (typeof n !== "number" || !isFinite(n) || n <= 0) return null;
    const h = Math.floor(n / 60);
    const m = n % 60;
    if (h === 0) return `${m} min`;
    if (m === 0) return `${h} h`;
    return `${h} h ${String(m).padStart(2, "0")}`;
  }

  // Storage key for "checked" ingredients persisted per-recipe in localStorage.
  function checkedKey(recipeId) {
    return `cdr.checked.${recipeId}`;
  }
  function loadChecked(recipeId) {
    try {
      const raw = localStorage.getItem(checkedKey(recipeId));
      if (!raw) return new Set();
      const arr = JSON.parse(raw);
      return new Set(Array.isArray(arr) ? arr : []);
    } catch (_) {
      return new Set();
    }
  }
  function saveChecked(recipeId, set) {
    try {
      localStorage.setItem(checkedKey(recipeId), JSON.stringify([...set]));
    } catch (_) {
      /* quota / private mode — silently ignore */
    }
  }

  // ---------- category icons ----------
  // Hand-drawn line-art SVGs, single-color (currentColor), 48x48 viewBox.
  const CATEGORY_ICONS = {
    "les-buffet-et-hors-d-oeuvres": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M5 34h38"/>
        <path d="M9 34a15 15 0 0 1 30 0"/>
        <circle cx="24" cy="14" r="2" fill="currentColor"/>
        <path d="M24 16v3"/>
        <circle cx="16" cy="22" r="1.5" fill="currentColor"/>
        <circle cx="32" cy="22" r="1.5" fill="currentColor"/>
      </svg>`,
    "les-soupes": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M18 16c0-3 3-3 3-6s-3-3-3-6"/>
        <path d="M24 18c0-3 3-3 3-6s-3-3-3-6"/>
        <path d="M30 16c0-3 3-3 3-6s-3-3-3-6"/>
        <path d="M7 24h34"/>
        <path d="M9 24a15 15 0 0 0 30 0"/>
      </svg>`,
    "brunch-et-dejeuner": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M18 10c0-2 2-2 2-4s-2-2-2-4"/>
        <path d="M24 10c0-2 2-2 2-4s-2-2-2-4"/>
        <path d="M30 10c0-2 2-2 2-4s-2-2-2-4"/>
        <path d="M8 18h26v12a8 8 0 0 1-8 8H16a8 8 0 0 1-8-8z"/>
        <path d="M34 22h4a4 4 0 0 1 0 8h-4"/>
        <path d="M6 42h32"/>
      </svg>`,
    "les-mets-principaux": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="24" cy="26" r="11"/>
        <circle cx="24" cy="26" r="6"/>
        <path d="M8 6v10a2 2 0 0 0 2 2v26"/>
        <path d="M10 6v10"/>
        <path d="M12 6v10a2 2 0 0 1-2 2"/>
        <path d="M40 6c-2 0-3 4-3 8v6h3z"/>
        <path d="M40 20v22"/>
      </svg>`,
    "biscuits": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="24" cy="24" r="16"/>
        <circle cx="18" cy="18" r="1.6" fill="currentColor"/>
        <circle cx="30" cy="20" r="1.6" fill="currentColor"/>
        <circle cx="22" cy="29" r="1.6" fill="currentColor"/>
        <circle cx="31" cy="30" r="1.6" fill="currentColor"/>
        <circle cx="14" cy="26" r="1.6" fill="currentColor"/>
      </svg>`,
    "desserts": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M8 40 L24 12 L40 40 Z"/>
        <path d="M14 28 q3 -3 6 0 t6 0 t6 0"/>
        <circle cx="24" cy="9" r="2.2"/>
        <path d="M24 7 q1 -3 4 -3"/>
      </svg>`,
    "tartes": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="24" cy="24" r="16"/>
        <circle cx="24" cy="24" r="13" stroke-dasharray="2 2"/>
        <path d="M11 24h26"/>
        <path d="M24 11v26"/>
        <path d="M14 14l20 20"/>
        <path d="M34 14L14 34"/>
      </svg>`,
    "les-sauces": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M8 22h28l-3 12a4 4 0 0 1-4 3H15a4 4 0 0 1-4-3z"/>
        <path d="M36 22l6-4-3 9"/>
        <path d="M8 24c-3 0-3 6 0 6"/>
        <path d="M40 14l2 -3"/>
      </svg>`,
    "les-epices": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M8 26h32"/>
        <path d="M10 26a14 14 0 0 0 28 0"/>
        <line x1="22" y1="28" x2="38" y2="8"/>
        <circle cx="38" cy="8" r="3" fill="currentColor"/>
        <circle cx="18" cy="34" r="1" fill="currentColor"/>
        <circle cx="24" cy="36" r="1" fill="currentColor"/>
        <circle cx="30" cy="34" r="1" fill="currentColor"/>
      </svg>`,
    "drinks": `
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M14 6h20l-2 14a8 8 0 0 1-16 0z"/>
        <line x1="24" y1="28" x2="24" y2="40"/>
        <line x1="14" y1="42" x2="34" y2="42"/>
      </svg>`,
  };

  const DEFAULT_CATEGORY_ICON = `
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M8 40h32"/>
      <path d="M12 40v-8a12 12 0 0 1 24 0v8"/>
      <circle cx="24" cy="14" r="2" fill="currentColor"/>
    </svg>`;

  function categoryIcon(slug) {
    return CATEGORY_ICONS[slug] || DEFAULT_CATEGORY_ICON;
  }

  // ---------- filter taxonomy ----------
  // Tags are grouped so within-group selections OR together (e.g. boeuf OR poulet),
  // while groups AND across each other (poulet AND rapide). Mirrors a faceted search.
  const TAG_GROUPS = [
    {
      key: "diet",
      label: "Régime",
      tags: [
        // Manually-authored in recipe meta.tags
        "sans-gluten", "vegetarien",
        // Auto-classified from ingredients (covers all 598 recipes)
        "vegan", "pescatarien",
        // Estimated from per-serving nutrition (covers ~198 recipes — see UI hint)
        "faible-sucre", "faible-sel", "faible-gras", "faible-glucides",
        "riche-proteines", "riche-fibres", "diabetique", "keto",
      ],
    },
    {
      key: "method",
      label: "Cuisson",
      tags: [
        "four", "micro-ondes", "mijoteuse", "sans-cuisson",
        // Future-use methods — no recipes carry these tags today; tag manually
        // as new recipes using these appliances are added to recipes.json.
        "sous-vide", "air-fryer", "bbq", "fumoir",
        "plaque-a-griller", "vapeur",
      ],
    },
    { key: "other",   label: "Autre",     tags: ["congelation", "conserves", "festif"] },
  ];

  // Pretty labels for the new tags. Existing tags fall back to their slug.
  const TAG_LABELS = {
    "sans-gluten":      "Sans gluten",
    "vegetarien":       "Végétarien",
    "vegan":            "Végétalien",
    "pescatarien":      "Pescétarien",
    "faible-sucre":     "Faible en sucre",
    "faible-sel":       "Faible en sel",
    "faible-gras":      "Faible en gras",
    "faible-glucides":  "Faible en glucides",
    "riche-proteines":  "Riche en protéines",
    "riche-fibres":     "Riche en fibres",
    "diabetique":       "Diabétique",
    "keto":             "Keto",
    // Cuisson — future-use cooking methods (manual tagging)
    "sous-vide":        "Sous vide",
    "air-fryer":        "Air fryer",
    "bbq":              "BBQ",
    "fumoir":           "Fumoir",
    "plaque-a-griller": "Plaque à griller",
    "vapeur":           "À la vapeur",
  };
  const DIFFICULTIES = ["facile", "moyen", "difficile"];
  // Buckets on prep + cook total. Keys are independent of the difficulty "moyen".
  const TIME_BUCKETS = [
    { key: "tb-rapide", label: "Rapide", hint: "≤ 30 min", min: 0,  max: 30  },
    { key: "tb-moyen",  label: "Moyen",  hint: "31–60 min", min: 31, max: 60 },
    { key: "tb-long",   label: "Long",   hint: "> 60 min", min: 61, max: Infinity },
  ];

  // ---------- ingredient picker ----------
  // Hand-drawn line-art icons matching the cahier aesthetic — viewBox 24x24,
  // currentColor stroke, no fill. Each ingredient also has match patterns
  // applied to normalized (lowercased + ligature/diacritic-stripped) text.
  const ING_SVG = (paths) =>
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
  const ING_DEFAULT_ICON = ING_SVG('<circle cx="12" cy="12" r="7"/><path d="M9 10c1 -1 4 -1 6 0"/>');

  const INGREDIENTS = {
    oignon:        { label: "Oignon",          patterns: [/\boignon/], icon: ING_SVG('<path d="M12 4c-1 0 -1 -2 0 -2"/><path d="M12 4c1 0 1 -2 0 -2"/><path d="M5.5 13a6.5 7 0 0 0 13 0c0 -3.5 -3 -7 -6.5 -7s-6.5 3.5 -6.5 7z"/><path d="M9 9c-1 4 -1 8 0 11"/><path d="M15 9c1 4 1 8 0 11"/>') },
    ail:           { label: "Ail",             patterns: [/\bail\b/, /\bgousse/], icon: ING_SVG('<path d="M12 4c-1 0 0 -2 0 -2"/><path d="M12 4c1 0 0 -2 0 -2"/><path d="M6 13a6 7 0 0 0 12 0c0 -4 -3 -7 -6 -7s-6 3 -6 7z"/><path d="M12 6v15"/><path d="M9 8c-1 4 -1 9 -1 13"/><path d="M15 8c1 4 1 9 1 13"/>') },
    carotte:       { label: "Carotte",         patterns: [/\bcarotte/], icon: ING_SVG('<path d="M9 9l3 12 3 -12z"/><path d="M9 9q-2 -3 0 -5"/><path d="M12 9q0 -3 0 -5"/><path d="M15 9q2 -3 0 -5"/><path d="M10 13h4"/><path d="M11 16h2"/>') },
    celeri:        { label: "Céleri",          patterns: [/\bceleri/], icon: ING_SVG('<path d="M9 5v15"/><path d="M12 5v15"/><path d="M15 5v15"/><path d="M9 5q-1 -2 0 -3"/><path d="M12 5q1 -2 2 -3"/><path d="M15 5q-1 -2 -2 -3"/><path d="M7 20h10"/>') },
    tomate:        { label: "Tomate",          patterns: [/\btomate/], icon: ING_SVG('<circle cx="12" cy="14" r="6"/><path d="M12 8v-2"/><path d="M12 6l-2 -2"/><path d="M12 6l2 -2"/><path d="M12 6l-1 -3"/>') },
    patate:        { label: "Pomme de terre",  patterns: [/\bpommes? de terre/, /\bpatate/], icon: ING_SVG('<path d="M5 11c0 -4 4 -7 8 -6s7 4 6 8s-5 6 -9 5s-5 -3 -5 -7z"/><circle cx="10" cy="11" r=".4" fill="currentColor"/><circle cx="14" cy="13" r=".4" fill="currentColor"/><circle cx="11" cy="15" r=".4" fill="currentColor"/>') },
    mais:          { label: "Maïs",            patterns: [/\bmais\b/], icon: ING_SVG('<path d="M9 4q-2 6 0 16q3 -1 6 0q2 -10 0 -16z"/><path d="M9 4q-3 0 -3 -3"/><path d="M15 4q3 0 3 -3"/><path d="M10 7h4"/><path d="M10 10h4"/><path d="M10 13h4"/><path d="M10 16h4"/>') },
    champignon:    { label: "Champignon",      patterns: [/\bchampignon/], icon: ING_SVG('<path d="M5 12a7 4 0 0 1 14 0z"/><path d="M9 12v6q3 1 6 0v-6"/><circle cx="10" cy="10" r=".5" fill="currentColor"/><circle cx="14" cy="11" r=".5" fill="currentColor"/>') },
    chou:          { label: "Chou",            patterns: [/\bchou/], icon: ING_SVG('<circle cx="12" cy="12" r="7.5"/><path d="M9 8q3 4 6 0"/><path d="M8 12q4 5 8 0"/><path d="M9 16q3 3 6 0"/>') },
    pois:          { label: "Pois",            patterns: [/\bpois\b/], icon: ING_SVG('<path d="M5 14q4 -8 14 -6q-4 8 -14 6z"/><circle cx="9" cy="12" r="1.3"/><circle cx="12" cy="11" r="1.3"/><circle cx="15" cy="10" r="1.3"/>') },
    haricot:       { label: "Haricots",        patterns: [/\bharicot/, /\bfeve/], icon: ING_SVG('<path d="M5 16q4 -10 14 -10q-4 12 -14 10z"/><path d="M7 14q4 -8 12 -8"/>') },
    courge:        { label: "Courge",          patterns: [/\bcitrouille/, /\bpotiron/, /\bcourge/], icon: ING_SVG('<path d="M12 7c-5 0 -8 3 -8 7s3 6 8 6s8 -2 8 -6s-3 -7 -8 -7z"/><path d="M12 7v13"/><path d="M8 8q-1 6 0 11"/><path d="M16 8q1 6 0 11"/><path d="M12 7q0 -2 2 -3"/>') },
    poivron:       { label: "Poivron",         patterns: [/\bpoivron/], icon: ING_SVG('<path d="M9 6h6v2q4 0 4 5v6q0 4 -7 4t-7 -4v-6q0 -5 4 -5z"/><path d="M11 6v-2"/><path d="M12 6v-2"/>') },
    epinard:       { label: "Épinards",        patterns: [/\bepinard/], icon: ING_SVG('<path d="M12 4q-6 4 -6 10q3 6 6 6q3 0 6 -6q0 -6 -6 -10z"/><path d="M12 5v15"/><path d="M12 9q-3 0 -4 2"/><path d="M12 9q3 0 4 2"/><path d="M12 14q-3 0 -4 2"/><path d="M12 14q3 0 4 2"/>') },

    poulet:        { label: "Poulet",          patterns: [/\bpoulet/], icon: ING_SVG('<path d="M14 5a3 3 0 0 0 -3 3l-6 9a2 2 0 0 0 2 2l1 -1a2 2 0 0 0 2 -2l5 -7a3 3 0 0 0 -1 -4z"/><circle cx="14.5" cy="5.5" r="2.5"/>') },
    boeuf:         { label: "Bœuf",            patterns: [/\bboeuf/, /\bbifteck/, /\bsteak/], icon: ING_SVG('<path d="M5 12c0 -4 3 -6 7 -6s5 1 6 4s-1 5 -3 6s-5 0 -7 -1s-3 -1 -3 -3z"/><path d="M9 11q3 -2 6 0"/>') },
    veau:          { label: "Veau",            patterns: [/\bveau\b/], icon: ING_SVG('<path d="M6 12c0 -3 3 -5 6 -5s6 2 6 5s-3 5 -6 5s-6 -2 -6 -5z"/><path d="M12 9v6"/><path d="M11 9h2"/><path d="M11 15h2"/>') },
    agneau:        { label: "Agneau",          patterns: [/\bagneau/, /\bmouton/], icon: ING_SVG('<circle cx="9" cy="14" r="5"/><path d="M13 11l6 -5"/><circle cx="19" cy="5.5" r="1.2"/><path d="M9 11q1 1 0 2"/>') },
    porc:          { label: "Porc",            patterns: [/\bporc\b/], icon: ING_SVG('<circle cx="12" cy="13" r="6"/><path d="M10 13a1 1 0 0 0 0 2"/><path d="M14 13a1 1 0 0 0 0 2"/><path d="M8 8l-2 -2l1 3"/><path d="M16 8l2 -2l-1 3"/>') },
    jambon:        { label: "Jambon",          patterns: [/\bjambon/], icon: ING_SVG('<path d="M5 14c0 -4 5 -7 9 -6s6 5 4 8s-7 4 -10 2s-3 -1 -3 -4z"/><path d="M14 8l3 -2l-1 3"/>') },
    bacon:         { label: "Bacon",            patterns: [/\bbacon\b/, /\blard\b/], icon: ING_SVG('<path d="M4 8q4 -3 8 0t8 0v3q-4 3 -8 0t-8 0z"/><path d="M4 14q4 -3 8 0t8 0v3q-4 3 -8 0t-8 0z"/>') },
    saucisse:      { label: "Saucisse",         patterns: [/\bsaucisse/], icon: ING_SVG('<path d="M5 9a3 3 0 0 1 3 -3l9 0a3 3 0 0 1 3 3l0 6a3 3 0 0 1 -3 3l-9 0a3 3 0 0 1 -3 -3z"/><path d="M7 9q1 1 0 2"/><path d="M17 13q1 1 0 2"/>') },
    poisson:       { label: "Poisson",         patterns: [/\bpoisson/, /\bsaumon/, /\bmorue/, /\bthon\b/], icon: ING_SVG('<path d="M3 12q3 -5 9 -5t9 5q-3 5 -9 5t-9 -5z"/><path d="M21 12l3 -3v6z"/><circle cx="7" cy="11" r=".5" fill="currentColor"/>') },
    "fruits-de-mer":{ label: "Fruits de mer",  patterns: [/\bfruits? de mer/, /\bcrevette/, /\bhomard/, /\bcrabe/, /\bpetoncle/, /\bhuitre/, /\bcalmar/, /\bcalamar/, /\blangoustine/], icon: ING_SVG('<path d="M5 16c-1 -5 4 -9 9 -7s5 7 2 9c-3 1 -7 1 -10 -1z"/><path d="M14 9l4 -4"/><path d="M16 11l4 -2"/><path d="M5 16l-2 1l1 -2"/><circle cx="11" cy="12" r=".5" fill="currentColor"/>') },

    beurre:        { label: "Beurre",          patterns: [/\bbeurre\b/], icon: ING_SVG('<path d="M4 9h16v6h-16z"/><path d="M4 11h16"/><path d="M16 9v6"/>') },
    lait:          { label: "Lait",            patterns: [/\blait\b/], icon: ING_SVG('<path d="M7 7v12h10v-12"/><path d="M7 7l3 -3h4l3 3"/><path d="M10 4v3"/><path d="M9 13h6"/>') },
    creme:         { label: "Crème",           patterns: [/\bcreme\b/], icon: ING_SVG('<path d="M7 9c0 6 1 11 5 11s5 -5 5 -11"/><path d="M7 9q5 -2 10 0"/><path d="M9 9v-3h6v3"/>') },
    fromage:       { label: "Fromage",         patterns: [/\bfromage/], icon: ING_SVG('<path d="M5 16l14 -8v8z"/><circle cx="12" cy="13" r=".7" fill="currentColor"/><circle cx="15" cy="11.5" r=".5" fill="currentColor"/><circle cx="9" cy="14.5" r=".5" fill="currentColor"/>') },
    oeuf:          { label: "Œufs",            patterns: [/\boeuf/], icon: ING_SVG('<path d="M12 4c-3 0 -5 4 -5 8a5 5 0 0 0 10 0c0 -4 -2 -8 -5 -8z"/>') },

    pomme:         { label: "Pomme",           patterns: [/\bpomme(?!s? de terre)/], icon: ING_SVG('<path d="M12 7c-3 -2 -7 -1 -7 4c0 5 4 8 7 8s7 -3 7 -8c0 -5 -4 -6 -7 -4z"/><path d="M12 7q1 -2 3 -2"/><path d="M12 7v-1"/>') },
    citron:        { label: "Citron",          patterns: [/\bcitron/], icon: ING_SVG('<path d="M12 5q5 1 5 7q0 6 -5 7q-5 -1 -5 -7q0 -6 5 -7z"/><path d="M12 5v-1"/><path d="M12 19v1"/>') },
    orange:        { label: "Orange",          patterns: [/\borange/], icon: ING_SVG('<circle cx="12" cy="13" r="6"/><path d="M12 7v-1"/><path d="M12 6q-2 -2 -4 -2q1 1 1 2"/>') },
    fraise:        { label: "Fraise",          patterns: [/\bfraise/], icon: ING_SVG('<path d="M12 8c-3 0 -5 2 -5 5c0 4 5 7 5 7s5 -3 5 -7c0 -3 -2 -5 -5 -5z"/><path d="M9 7q3 -2 6 0"/><path d="M12 5v3"/><circle cx="10" cy="12" r=".4" fill="currentColor"/><circle cx="14" cy="13" r=".4" fill="currentColor"/><circle cx="12" cy="15" r=".4" fill="currentColor"/>') },
    raisins:       { label: "Raisins",         patterns: [/\braisin/], icon: ING_SVG('<path d="M12 5v3"/><circle cx="9" cy="10" r="1.5"/><circle cx="12" cy="10" r="1.5"/><circle cx="15" cy="10" r="1.5"/><circle cx="10.5" cy="13" r="1.5"/><circle cx="13.5" cy="13" r="1.5"/><circle cx="12" cy="16" r="1.5"/>') },

    farine:        { label: "Farine",          patterns: [/\bfarine/], icon: ING_SVG('<path d="M9 6l-3 -2l3 1"/><path d="M15 6l3 -2l-3 1"/><path d="M7 7h10v12h-10z"/><path d="M9 13q3 -1 6 0"/>') },
    sucre:         { label: "Sucre",           patterns: [/\bsucre(?! a glacer)/], icon: ING_SVG('<path d="M5 9l7 -4l7 4l-7 4z"/><path d="M5 9v6l7 4v-6"/><path d="M19 9v6l-7 4"/>') },
    cassonade:     { label: "Cassonade",       patterns: [/\bcassonade/], icon: ING_SVG('<path d="M5 14h14v5h-14z"/><path d="M5 14q7 -8 14 0"/><circle cx="9" cy="12" r=".4" fill="currentColor"/><circle cx="12" cy="11" r=".4" fill="currentColor"/><circle cx="15" cy="12" r=".4" fill="currentColor"/>') },
    "sirop-erable":{ label: "Sirop d'érable",  patterns: [/sirop d'erable/, /sirop derable/], icon: ING_SVG('<path d="M12 4l1 3l3 -1l-1 3l3 1l-3 2l1 3l-3 -1l-1 4l-1 -4l-3 1l1 -3l-3 -2l3 -1l-1 -3l3 1z"/>') },
    levure:        { label: "Levure",          patterns: [/\blevure/, /\bpoudre a pate/], icon: ING_SVG('<path d="M7 7h10v13h-10z"/><path d="M7 7q1 -1 2 0t2 0t2 0t2 0t2 0"/><path d="M11 12h2"/><path d="M10 14l2 3l2 -3"/>') },
    chocolat:      { label: "Chocolat",        patterns: [/\bchocolat/], icon: ING_SVG('<path d="M5 7h14v10h-14z"/><path d="M5 12h14"/><path d="M10 7v10"/><path d="M14 7v10"/>') },
    noix:          { label: "Noix",            patterns: [/\bnoix\b/, /\bnoisette/, /\bamande/, /\bpacane/], icon: ING_SVG('<path d="M5 9q3 -3 7 -1q3 -2 7 1c1 4 -1 7 -3 6q-3 4 -7 0q-3 1 -4 -6z"/><path d="M12 8v9"/>') },
    riz:           { label: "Riz",             patterns: [/\briz\b/], icon: ING_SVG('<path d="M4 13h16q-1 6 -8 6t-8 -6z"/><path d="M9 11q1 -1 2 0"/><path d="M12 10q1 -1 2 0"/><path d="M15 11q1 -1 2 0"/>') },
    pates:         { label: "Pâtes",           patterns: [/\bpates\b/, /\bspaghetti/, /\bmacaroni/], icon: ING_SVG('<path d="M4 8q5 -3 10 0t6 0"/><path d="M4 12q5 -3 10 0t6 0"/><path d="M4 16q5 -3 10 0t6 0"/>') },
    pain:          { label: "Pain",            patterns: [/\bpain\b/, /\bchapelure/], icon: ING_SVG('<path d="M4 14a8 8 0 0 1 16 0v3h-16z"/><path d="M8 11l1 1"/><path d="M12 11l1 1"/><path d="M16 11l1 1"/>') },
    vinaigre:      { label: "Vinaigre",        patterns: [/\bvinaigre/], icon: ING_SVG('<path d="M10 4v3q-2 1 -2 4v9a1 1 0 0 0 1 1h6a1 1 0 0 0 1 -1v-9q0 -3 -2 -4v-3z"/><path d="M9 13h6"/>') },
    huile:         { label: "Huile",           patterns: [/\bhuile/], icon: ING_SVG('<path d="M10 4v3q-2 1 -2 4v9a1 1 0 0 0 1 1h6a1 1 0 0 0 1 -1v-9q0 -3 -2 -4v-3z"/><path d="M12 13q-1.5 1.5 0 3q1.5 -1.5 0 -3z"/>') },
    moutarde:      { label: "Moutarde",        patterns: [/\bmoutarde/], icon: ING_SVG('<path d="M7 9v10h10v-10z"/><path d="M6 7h12v2h-12z"/><path d="M9 12h6"/><path d="M9 15h6"/>') },
    bouillon:      { label: "Bouillon",        patterns: [/\bbouillon/], icon: ING_SVG('<path d="M5 11v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1 -1v-8z"/><path d="M4 11h16"/><path d="M3 12h2"/><path d="M19 12h2"/><path d="M9 8q1 -2 0 -3"/><path d="M12 8q1 -2 0 -3"/><path d="M15 8q1 -2 0 -3"/>') },

    persil:        { label: "Persil",           patterns: [/\bpersil/], icon: ING_SVG('<path d="M12 4v16"/><path d="M12 8q-3 -1 -3 -4"/><path d="M12 8q3 -1 3 -4"/><path d="M12 13q-3 -1 -3 -4"/><path d="M12 13q3 -1 3 -4"/>') },
    thym:          { label: "Thym",             patterns: [/\bthym/], icon: ING_SVG('<path d="M12 4v16"/><circle cx="10" cy="8" r=".7" fill="currentColor"/><circle cx="14" cy="9" r=".7" fill="currentColor"/><circle cx="10" cy="12" r=".7" fill="currentColor"/><circle cx="14" cy="13" r=".7" fill="currentColor"/><circle cx="10" cy="16" r=".7" fill="currentColor"/>') },
    piment:        { label: "Piment",           patterns: [/\bpiment/, /\bcayenne/, /\bchili\b/], icon: ING_SVG('<path d="M11 5q-1 0 -1 1q0 1 1 1"/><path d="M11 7c-3 0 -5 3 -3 7s4 6 7 4c2 -2 2 -7 -1 -10c-1 -1 -2 -1 -3 -1z"/>') },
    laurier:       { label: "Laurier",          patterns: [/\blaurier/], icon: ING_SVG('<path d="M12 3q-4 4 -4 9q0 5 4 9q4 -4 4 -9q0 -5 -4 -9z"/><path d="M12 3v18"/>') },
    vanille:       { label: "Vanille",          patterns: [/\bvanille/], icon: ING_SVG('<path d="M5 19l14 -14"/><path d="M5 19q-1 -2 1 -2"/><path d="M19 5q1 2 -1 2"/><path d="M7 17q1 1 2 0"/><path d="M15 9q1 -1 2 0"/>') },
    basilic:       { label: "Basilic",          patterns: [/\bbasilic/], icon: ING_SVG('<path d="M12 5q-5 1 -6 7q-1 5 6 7q7 -2 6 -7q-1 -6 -6 -7z"/><path d="M12 5v14"/><path d="M12 9q-3 0 -4 2"/><path d="M12 9q3 0 4 2"/><path d="M12 14q-3 0 -4 2"/><path d="M12 14q3 0 4 2"/>') },
    paprika:       { label: "Paprika",          patterns: [/\bpaprika/], icon: ING_SVG('<path d="M9 7h6v2q2 1 2 4v8a1 1 0 0 1 -1 1h-8a1 1 0 0 1 -1 -1v-8q0 -3 2 -4z"/><path d="M11 7v-2h2v2"/><circle cx="11" cy="12" r=".4" fill="currentColor"/><circle cx="14" cy="13" r=".4" fill="currentColor"/><circle cx="11" cy="15" r=".4" fill="currentColor"/><circle cx="14" cy="16" r=".4" fill="currentColor"/>') },
    gingembre:     { label: "Gingembre",        patterns: [/\bgingembre/], icon: ING_SVG('<path d="M5 12q0 -3 3 -3q3 -3 6 0q4 -2 6 1q2 4 -1 6q-3 4 -7 2q-4 1 -6 -2q-2 -2 -1 -4z"/><path d="M9 11q1 2 0 3"/><path d="M14 10q1 2 0 3"/>') },
    ciboulette:    { label: "Ciboulette",       patterns: [/\bciboulette/], icon: ING_SVG('<path d="M8 7v13"/><path d="M11 5v15"/><path d="M14 7v13"/><path d="M10 6v14"/><path d="M13 6v14"/><circle cx="11" cy="4" r="1.5"/>') },
    curry:         { label: "Curry / Cari",     patterns: [/\bcurry\b/, /\bcari\b/, /\bkari\b/], icon: ING_SVG('<path d="M9 7h6v2q2 1 2 4v8a1 1 0 0 1 -1 1h-8a1 1 0 0 1 -1 -1v-8q0 -3 2 -4z"/><path d="M11 7v-2h2v2"/><circle cx="11" cy="13" r=".5" fill="currentColor"/><circle cx="14" cy="14" r=".5" fill="currentColor"/><circle cx="12" cy="16" r=".5" fill="currentColor"/><path d="M10 18h4"/>') },
    fenouil:       { label: "Fenouil",          patterns: [/\bfenouil/], icon: ING_SVG('<path d="M8 13q4 -4 8 0v6q-4 3 -8 0z"/><path d="M10 13v-6"/><path d="M12 13v-8"/><path d="M14 13v-6"/><path d="M9 8q-1 -1 -2 0"/><path d="M15 8q1 -1 2 0"/><path d="M11 6q-1 -1 -2 -1"/><path d="M13 6q1 -1 2 -1"/>') },
    cannelle:      { label: "Cannelle",         patterns: [/\bcannelle/], icon: ING_SVG('<path d="M5 9h14v6h-14z"/><path d="M5 9q3 3 0 6"/><path d="M19 9q-3 3 0 6"/><path d="M9 9q1 3 0 6"/><path d="M14 9q1 3 0 6"/>') },
    origan:        { label: "Origan",           patterns: [/\borigan/], icon: ING_SVG('<path d="M12 4v16"/><ellipse cx="9.5" cy="8" rx="1.5" ry="1"/><ellipse cx="14.5" cy="9" rx="1.5" ry="1"/><ellipse cx="9.5" cy="13" rx="1.5" ry="1"/><ellipse cx="14.5" cy="14" rx="1.5" ry="1"/><ellipse cx="9.5" cy="18" rx="1.5" ry="1"/>') },
    cumin:         { label: "Cumin",            patterns: [/\bcumin/], icon: ING_SVG('<ellipse cx="8" cy="9" rx="1.6" ry=".7" transform="rotate(-20 8 9)"/><ellipse cx="13" cy="8" rx="1.6" ry=".7" transform="rotate(15 13 8)"/><ellipse cx="10" cy="13" rx="1.6" ry=".7" transform="rotate(-10 10 13)"/><ellipse cx="15" cy="13" rx="1.6" ry=".7" transform="rotate(20 15 13)"/><ellipse cx="9" cy="17" rx="1.6" ry=".7" transform="rotate(10 9 17)"/><ellipse cx="14" cy="17" rx="1.6" ry=".7" transform="rotate(-15 14 17)"/>') },
    coriandre:     { label: "Coriandre",        patterns: [/\bcoriandre/], icon: ING_SVG('<path d="M12 4v16"/><path d="M9 8q-3 1 -3 -2q3 0 3 2z"/><path d="M15 8q3 1 3 -2q-3 0 -3 2z"/><path d="M8 13q-3 1 -3 -2q3 0 3 2z"/><path d="M16 13q3 1 3 -2q-3 0 -3 2z"/><path d="M9 18q-3 1 -3 -2q3 0 3 2z"/><path d="M15 18q3 1 3 -2q-3 0 -3 2z"/>') },
    muscade:       { label: "Muscade",          patterns: [/\bmuscade/], icon: ING_SVG('<ellipse cx="12" cy="12" rx="5" ry="4"/><path d="M9 9q0 3 0 6"/><path d="M12 8v8"/><path d="M15 9q0 3 0 6"/>') },
    romarin:       { label: "Romarin",          patterns: [/\bromarin/], icon: ING_SVG('<path d="M8 20l8 -16"/><path d="M11 16l-3 -1"/><path d="M13 13l-4 -1"/><path d="M14 10l-4 -1"/><path d="M16 7l-3 -1"/>') },
    aneth:         { label: "Aneth",            patterns: [/\baneth/], icon: ING_SVG('<path d="M12 4v16"/><path d="M12 6q-3 1 -4 4"/><path d="M12 6q3 1 4 4"/><path d="M12 11q-3 1 -4 3"/><path d="M12 11q3 1 4 3"/><path d="M12 16q-2 1 -3 2"/><path d="M12 16q2 1 3 2"/>') },
  };

  const INGREDIENT_GROUPS = [
    { label: "Légumes",                  slugs: ["oignon","ail","carotte","celeri","tomate","patate","mais","champignon","chou","pois","haricot","courge","poivron","epinard"] },
    { label: "Viandes & poissons",       slugs: ["poulet","boeuf","veau","agneau","porc","jambon","bacon","saucisse","poisson","fruits-de-mer"] },
    { label: "Produits laitiers & œufs", slugs: ["beurre","lait","creme","fromage","oeuf"] },
    { label: "Fruits",                   slugs: ["pomme","citron","orange","fraise","raisins"] },
    { label: "Épices & herbes",          slugs: ["persil","thym","piment","laurier","vanille","basilic","paprika","gingembre","ciboulette","curry","fenouil","cannelle","origan","cumin","coriandre","muscade","romarin","aneth"] },
    { label: "Garde-manger",             slugs: ["farine","sucre","cassonade","sirop-erable","levure","chocolat","noix","riz","pates","pain","vinaigre","huile","moutarde","bouillon"] },
  ];

  // Recipes pre-indexed by ingredient slug after data loads.
  let recipeIngredientSlugs = new WeakMap();

  function indexRecipeIngredients() {
    recipeIngredientSlugs = new WeakMap();
    for (const r of recipes) {
      const ingText = normalizeText((r.ingredients || []).join("  "));
      const hits = new Set();
      for (const slug of Object.keys(INGREDIENTS)) {
        const def = INGREDIENTS[slug];
        if (def.patterns.some((p) => p.test(ingText))) hits.add(slug);
      }
      recipeIngredientSlugs.set(r, hits);
    }
  }

  const filterState = {
    difficulties: new Set(),
    timeBuckets: new Set(),
    tagsByGroup: Object.fromEntries(TAG_GROUPS.map((g) => [g.key, new Set()])),
    ingredients: new Set(),
  };

  function enviFilterActive() {
    return (
      filterState.difficulties.size > 0 ||
      filterState.timeBuckets.size > 0 ||
      Object.values(filterState.tagsByGroup).some((s) => s.size > 0)
    );
  }

  function anyFilterActive() {
    return enviFilterActive() || filterState.ingredients.size > 0;
  }

  function enviFilterCount() {
    let n = filterState.difficulties.size + filterState.timeBuckets.size;
    for (const s of Object.values(filterState.tagsByGroup)) n += s.size;
    return n;
  }

  function resetEnviFilters() {
    filterState.difficulties.clear();
    filterState.timeBuckets.clear();
    for (const s of Object.values(filterState.tagsByGroup)) s.clear();
  }

  function resetIngredients() {
    filterState.ingredients.clear();
  }

  // ---------- search UI state + persistence ----------
  // Persisted in sessionStorage under "cdr.search" so filters survive
  // navigation to/from a recipe within the same tab. Sets are stored as arrays.
  const uiState = {
    query: "",
    sort: "numero",
    openIngGroups: null, // Set<groupLabel> — null until first render
  };
  const SEARCH_STORAGE_KEY = "cdr.search";

  function saveSearchState() {
    try {
      const data = {
        q: uiState.query,
        sort: uiState.sort,
        diff: [...filterState.difficulties],
        tb: [...filterState.timeBuckets],
        tags: Object.fromEntries(
          Object.entries(filterState.tagsByGroup).map(([k, v]) => [k, [...v]]),
        ),
        ing: [...filterState.ingredients],
        open: uiState.openIngGroups ? [...uiState.openIngGroups] : null,
      };
      sessionStorage.setItem(SEARCH_STORAGE_KEY, JSON.stringify(data));
    } catch (_) {
      /* quota/private mode — ignore */
    }
  }

  function loadSearchState() {
    try {
      const raw = sessionStorage.getItem(SEARCH_STORAGE_KEY);
      if (!raw) return;
      const d = JSON.parse(raw);
      uiState.query = typeof d.q === "string" ? d.q : "";
      uiState.sort = typeof d.sort === "string" ? d.sort : "numero";
      filterState.difficulties = new Set(d.diff || []);
      filterState.timeBuckets = new Set(d.tb || []);
      for (const k of Object.keys(filterState.tagsByGroup)) {
        filterState.tagsByGroup[k] = new Set((d.tags || {})[k] || []);
      }
      filterState.ingredients = new Set(d.ing || []);
      uiState.openIngGroups = Array.isArray(d.open) ? new Set(d.open) : null;
    } catch (_) {
      /* corrupt — ignore */
    }
  }

  function totalMinutes(meta) {
    if (!meta) return 0;
    const p = typeof meta.prepMinutes === "number" ? meta.prepMinutes : 0;
    const c = typeof meta.cookMinutes === "number" ? meta.cookMinutes : 0;
    return p + c;
  }

  function recipeMatchesFilters(r) {
    const m = r.meta || {};
    if (filterState.difficulties.size && !filterState.difficulties.has(m.difficulty)) return false;
    if (filterState.timeBuckets.size) {
      const t = totalMinutes(m);
      const inAny = TIME_BUCKETS.some(
        (b) => filterState.timeBuckets.has(b.key) && t >= b.min && t <= b.max,
      );
      if (!inAny) return false;
    }
    // Recipe tags = manually-authored meta.tags + auto-classified régime tags.
    // The régime sidecar (dietTagsById) adds vegan/pescatarien plus all the
    // nutrient-based estimates without touching the source recipes.json.
    const recipeTags = new Set(m.tags || []);
    const dietTags = dietTagsById.get(r.id);
    if (dietTags) for (const t of dietTags) recipeTags.add(t);
    for (const g of TAG_GROUPS) {
      const sel = filterState.tagsByGroup[g.key];
      if (sel.size === 0) continue;
      let any = false;
      for (const t of sel) if (recipeTags.has(t)) { any = true; break; }
      if (!any) return false;
    }
    if (filterState.ingredients.size > 0) {
      const hits = recipeIngredientSlugs.get(r);
      if (!hits) return false;
      for (const slug of filterState.ingredients) if (!hits.has(slug)) return false;
    }
    return true;
  }

  // ---------- data ----------
  let recipes = [];
  let categories = [];
  let recipesById = new Map();
  let categoryBySlug = new Map();
  // Régime / diet sidecar — populated by loadData() when assets/diet_tags.json is present.
  // dietTagsById: Map<recipe.id, Set<string>>; nutrientTagSet flags which tags are
  // estimated from nutrition data (so the UI can show an "Estimé" badge).
  let dietTagsById = new Map();
  let nutrientTagSet = new Set();
  let dietCoverage = null;
  // Per-recipe nutrient panel data — populated by loadData() from
  // assets/recipes_nutrition.json. Map<recipe.id, slim nutrition record>.
  let nutritionByRecipeId = new Map();
  let nutritionConfig = null;        // { displayed_nutrients: [...] }

  async function loadData() {
    // diet_tags.json and recipes_nutrition.json are optional — if missing, the
    // régime filters and recipe-detail nutrient panel both degrade silently.
    const [r, c, d, n] = await Promise.all([
      fetch("recipes.json").then((x) => x.json()),
      fetch("categories.json").then((x) => x.json()),
      fetch("assets/diet_tags.json").then((x) => x.ok ? x.json() : null).catch(() => null),
      fetch("assets/recipes_nutrition.json").then((x) => x.ok ? x.json() : null).catch(() => null),
    ]);
    recipes = r;
    categories = c;
    recipesById = new Map(r.map((x) => [x.id, x]));
    categoryBySlug = new Map(c.map((cat) => [slugify(cat.name), cat]));
    if (d && d.tags_by_recipe) {
      dietTagsById = new Map(
        Object.entries(d.tags_by_recipe).map(([k, v]) => [Number(k), new Set(v)]),
      );
      dietCoverage = d.coverage || null;
      nutrientTagSet = new Set(d.nutrient_tags || []);
    }
    if (n && n.by_recipe) {
      nutritionByRecipeId = new Map(
        Object.entries(n.by_recipe).map(([k, v]) => [Number(k), v]),
      );
      nutritionConfig = { displayed_nutrients: n.displayed_nutrients || [] };
    }
    indexRecipeIngredients();
  }

  function recipesInCategory(cat) {
    return cat.recipeIds
      .map((id) => recipesById.get(id))
      .filter(Boolean);
  }

  function categoryForRecipe(recipeId) {
    return categories.find((c) => c.recipeIds.includes(recipeId)) || null;
  }

  // ---------- routing ----------
  function parseRoute() {
    let hash = location.hash.replace(/^#/, "");
    if (!hash || hash === "/") return { name: "home" };
    if (hash.startsWith("/")) hash = hash.slice(1);
    const parts = hash.split("/").filter(Boolean);
    const head = parts[0];
    if (head === "sommaire") return { name: "sommaire" };
    if (head === "recherche") return { name: "recherche" };
    if (head === "categorie" && parts[1])
      return { name: "categorie", slug: decodeURIComponent(parts[1]) };
    if (head === "recette" && parts[1])
      return { name: "recette", id: parseInt(parts[1], 10) };
    return { name: "home" };
  }

  function navigateTo(path) {
    if (!path.startsWith("#")) path = "#" + path;
    location.hash = path;
  }

  // ---------- shared chrome ----------
  // Auth state — populated on module load via onAuthChange below. The render
  // pipeline reads this when building the header so the Connexion / Déconnexion
  // affordance reflects the current session.
  let authSession = null;

  function authChip() {
    // Auth not configured yet (placeholder Supabase keys) — hide the chip
    // entirely so the public site looks unchanged before db/SETUP.md is run.
    if (!isAuthConfigured()) return "";
    if (authSession) {
      const email = (authSession.user?.email || "").toLowerCase();
      const initial = email ? email[0].toUpperCase() : "•";
      return `
        <button type="button" class="nav-user" data-action="signout"
                aria-label="Déconnexion (${escapeHtml(email)})"
                title="${escapeHtml(email)} — cliquez pour vous déconnecter">
          <span class="nav-user-dot" aria-hidden="true">${escapeHtml(initial)}</span>
          <span class="nav-user-label">Déconnexion</span>
        </button>`;
    }
    return `
      <a href="/login.html" class="nav-login" aria-label="Connexion">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
          <polyline points="10 17 15 12 10 7"/>
          <line x1="15" y1="12" x2="3" y2="12"/>
        </svg>
        <span class="nav-login-label">Connexion</span>
      </a>`;
  }

  function renderNav(active) {
    return `
      <header class="appnav">
        <div class="appnav-inner">
          <a href="#/" class="brand" aria-label="Cahier de Recettes">
            <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v17a1 1 0 0 1-1 1H6.5a2.5 2.5 0 0 1 0-5H20"></path>
            </svg>
            <span class="brand-text">Cahier de Recettes</span>
          </a>
          <div class="nav-sep"></div>
          <div class="nav-mid">
            <a href="#/sommaire" class="nav-pill ${active === "sommaire" ? "active" : ""}">Table des Matières</a>
          </div>
          <a href="#/recherche" class="nav-search ${active === "recherche" ? "active" : ""}" aria-label="Recherche">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.3-4.3"></path>
            </svg>
            <span class="nav-search-text">Recherche</span>
          </a>
          ${authChip()}
        </div>
      </header>
    `;
  }

  // ---------- views ----------
  function viewHome() {
    return `
      <section class="book-cover">
        <div class="cover-rule">
          <span class="cover-rule-text">Édition familiale</span>
          <div class="cover-rule-line"></div>
          <span class="cover-rule-text">2024</span>
        </div>
        <div class="cover-center">
          <div class="cover-divider">
            <div class="line"></div>
            <svg class="diamond" viewBox="0 0 8 8" fill="currentColor" aria-hidden="true"><polygon points="4,0 8,4 4,8 0,4"/></svg>
            <div class="line"></div>
          </div>
          <h1 class="cover-title">Cahier de<br><span class="it">Recettes</span></h1>
          <p class="cover-subtitle">Recettes de famille, transmises avec amour</p>
          <div class="cover-stats">
            <div class="cover-stat">
              <span class="num">${recipes.length}</span>
              <span class="label">Recettes</span>
            </div>
            <div class="cover-stat">
              <span class="num">${categories.length + 1}</span>
              <span class="label">Chapitres</span>
            </div>
          </div>
          <a href="#/sommaire" class="cta">
            Ouvrir le livre
            <svg class="cta-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </a>
        </div>
      </section>
    `;
  }

  function viewSommaire() {
    return `
      <section class="toc-page">
        <div class="container container-md">
          <header class="toc-header">
            <h1 class="toc-title">Table des Matières</h1>
            <div class="toc-orn">
              <div class="line"></div>
              <span class="dot"></span>
              <div class="line"></div>
            </div>
            <div class="toc-controls">
              <button type="button" id="toc-expand-all" class="toc-ctrl-btn">Tout déplier</button>
              <span class="toc-ctrl-sep">·</span>
              <button type="button" id="toc-collapse-all" class="toc-ctrl-btn">Tout replier</button>
            </div>
          </header>
          <div class="toc-sections">
            ${categories
              .map((cat) => {
                const items = recipesInCategory(cat);
                const slug = slugify(cat.name);
                return `
                  <details class="toc-section" data-cat-slug="${escapeHtml(slug)}">
                    <summary class="toc-cat-head">
                      <span class="toc-cat-icon">${categoryIcon(slug)}</span>
                      <h2 class="toc-cat-name">${escapeHtml(cat.name)}</h2>
                      <span class="toc-cat-count">${items.length} recettes</span>
                      <svg class="toc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
                    </summary>
                    <div class="toc-cat-body">
                      <a href="#/categorie/${encodeURIComponent(slug)}" class="toc-cat-page-link">
                        Voir la page de la catégorie
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                      </a>
                      <div class="toc-cat-grid">
                        ${items
                          .map(
                            (r) => `
                              <a href="#/recette/${r.id}" class="toc-recipe">
                                <span class="num">${pad3(r.id)}</span>
                                <span class="title">${escapeHtml(r.title)}</span>
                              </a>
                            `,
                          )
                          .join("")}
                      </div>
                    </div>
                  </details>
                `;
              })
              .join("")}
          </div>
        </div>
      </section>
    `;
  }

  function viewCategorie(slug) {
    const cat = categoryBySlug.get(slug);
    if (!cat) {
      return `
        <section class="empty-state" style="min-height:60vh; display:flex; align-items:center; justify-content:center;">
          <p>Catégorie introuvable.</p>
        </section>
      `;
    }
    const items = recipesInCategory(cat);
    return `
      <section class="cat-landing">
        <div class="cat-landing-inner">
          <div class="cat-landing-orn">
            <svg width="120" height="24" viewBox="0 0 120 24" fill="none" stroke="currentColor" aria-hidden="true">
              <path d="M0 12 L45 12 M75 12 L120 12" stroke-width="1"/>
              <circle cx="60" cy="12" r="4" fill="currentColor"/>
              <circle cx="50" cy="12" r="2"/>
              <circle cx="70" cy="12" r="2"/>
            </svg>
          </div>
          <h1 class="cat-landing-title">${escapeHtml(cat.name)}</h1>
          <p class="cat-landing-sub">${items.length} recettes soigneusement sélectionnées</p>
          ${
            items.length > 0
              ? `<a href="#/recette/${items[0].id}" class="cat-cta">Commencer la lecture</a>`
              : ""
          }
        </div>
      </section>
    `;
  }

  // Render the info strip (prep / cook / portions or yield) below the recipe title,
  // followed by the difficulty + tag chips row. Each element only renders if it has
  // a value, so recipes with no metadata fall back to the original ornament header.
  function renderInfoStrip(meta, recipeId = null) {
    if (!meta) return "";
    const items = [];
    const prep = formatMinutes(meta.prepMinutes);
    const cook = formatMinutes(meta.cookMinutes);
    const serv = typeof meta.servings === "number" ? meta.servings : null;
    const yc = typeof meta.yieldCount === "number" ? meta.yieldCount : null;
    const yu = typeof meta.yieldUnit === "string" ? meta.yieldUnit : null;

    if (prep) items.push({ label: "Préparation", value: prep, icon: "knife" });
    if (cook) items.push({ label: "Cuisson", value: cook, icon: "clock" });
    if (serv !== null) {
      items.push({
        label: serv > 1 ? "Portions" : "Portion",
        value: String(serv),
        icon: "people",
      });
    } else if (yc !== null && yu) {
      items.push({
        label: "Donne",
        value: `${yc} ${yu}`,
        icon: "yield",
      });
    } else if (yu && yc === null) {
      items.push({ label: "Donne", value: yu, icon: "yield" });
    }

    let strip = "";
    if (items.length > 0) {
      strip = `
        <div class="info-strip" role="list">
          ${items
            .map(
              (it) => `
                <div class="info-badge" role="listitem">
                  ${INFO_ICONS[it.icon]}
                  <div class="info-text">
                    <span class="info-label">${escapeHtml(it.label)}</span>
                    <span class="info-value">${escapeHtml(it.value)}</span>
                  </div>
                </div>
              `,
            )
            .join("")}
        </div>
      `;
    }

    const chips = [];
    if (meta.difficulty) {
      chips.push(`<span class="chip chip-difficulty chip-${escapeHtml(meta.difficulty)}">${escapeHtml(meta.difficulty)}</span>`);
    }
    // Union manually-authored meta.tags with auto-classified régime tags.
    // Keep insertion order (manual first) and dedupe.
    const seen = new Set();
    const tagsForRecipe = [];
    for (const t of (meta.tags || [])) {
      if (!seen.has(t)) { seen.add(t); tagsForRecipe.push(t); }
    }
    if (recipeId != null) {
      const ds = dietTagsById.get(recipeId);
      if (ds) for (const t of ds) if (!seen.has(t)) { seen.add(t); tagsForRecipe.push(t); }
    }
    for (const tag of tagsForRecipe) {
      const label = TAG_LABELS[tag] || tag.replace(/-/g, " ");
      const est   = nutrientTagSet.has(tag) ? ' data-est="1"' : "";
      chips.push(`<span class="chip chip-tag"${est}>${escapeHtml(label)}</span>`);
    }
    const chipsHtml = chips.length
      ? `<div class="info-chips">${chips.join("")}</div>`
      : "";

    return strip + chipsHtml;
  }

  // ---------- nutrient panel (recipe detail) ----------
  // Renders the per-serving nutrition table when assets/recipes_nutrition.json
  // covers this recipe. Returns "" when no estimate exists so the layout
  // collapses cleanly.
  function renderNutritionPanel(recipeId) {
    const n = nutritionByRecipeId.get(recipeId);
    if (!n) return "";
    const cfg = nutritionConfig?.displayed_nutrients || [];
    const ps = n.per_serving || {};
    const showPerServing = !n.servings_imputed && Object.keys(ps).length > 0;

    const fmt = (v, decimals) => {
      if (v == null || isNaN(v)) return "—";
      const factor = 10 ** decimals;
      return (Math.round(v * factor) / factor).toLocaleString("fr-CA", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    };

    // Build rows. We always show per-100g; per-serving only when servings is real.
    const rows = cfg.map((row) => {
      const ps100 = (n.per_100g || {})[row.id];
      const psServ = ps[row.id];
      const servingCell = showPerServing ? fmt(psServ, row.decimals) : "—";
      const cls = row.sub ? "nut-row nut-row-sub" : "nut-row";
      return `
        <tr class="${cls}">
          <th scope="row">${escapeHtml(row.label)}</th>
          <td class="nut-val">${servingCell}</td>
          <td class="nut-val">${fmt(ps100, row.decimals)}</td>
          <td class="nut-unit">${escapeHtml(row.unit)}</td>
        </tr>`;
    }).join("");

    // Header info: servings + a confidence note. Phrased gently — these are estimates.
    const matchPct = n.ingredient_count
      ? Math.round((n.match_count / n.ingredient_count) * 100)
      : 0;
    const confClass = n.low_conf_ratio > 0.30 ? "nut-conf-warn" : "nut-conf-ok";
    const skipNote = n.skipped_unquantified > 0
      ? ` · ${n.skipped_unquantified} ingrédient${n.skipped_unquantified > 1 ? "s" : ""} sans quantité ignoré${n.skipped_unquantified > 1 ? "s" : ""}`
      : "";
    const servHeader = showPerServing
      ? `Par portion (${n.servings})`
      : `Par portion <span class="nut-na">(non disponible)</span>`;
    const imputedHint = !showPerServing
      ? `<p class="nut-hint">Le nombre de portions n'est pas indiqué dans la recette — seules les valeurs par 100g sont calculées.</p>`
      : "";
    const lowConfHint = n.low_conf_ratio > 0.30
      ? `<p class="nut-hint nut-hint-warn">Estimation incertaine&nbsp;: ${Math.round(n.low_conf_ratio * 100)}% de la masse provient d'ingrédients à faible confiance${skipNote}.</p>`
      : "";

    return `
      <section class="nutrition-panel" aria-label="Information nutritionnelle">
        <div class="nut-header">
          <h3 class="nut-title">
            Information nutritionnelle
            <span class="nut-est-badge" title="Valeurs estimées à partir des ingrédients et de la base USDA">≈ Estimé</span>
          </h3>
          <p class="nut-meta ${confClass}">
            ${matchPct}% des ingrédients identifiés${skipNote ? " ·" + skipNote : ""}
          </p>
        </div>
        ${imputedHint}
        ${lowConfHint}
        <table class="nut-table">
          <thead>
            <tr>
              <th></th>
              <th>${servHeader}</th>
              <th>Pour 100g</th>
              <th></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </section>`;
  }

  // Hand-drawn line-art icons matching the cahier aesthetic (24x24, currentColor).
  const INFO_ICONS = {
    clock: `<svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="9"/>
              <polyline points="12 7 12 12 15 14"/>
            </svg>`,
    knife: `<svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M3 17l11-11a4 4 0 0 1 5.7 5.7L8.7 22.7a1 1 0 0 1-1.4 0L1.3 16.7a1 1 0 0 1 0-1.4z" transform="translate(1 -2)"/>
              <line x1="13" y1="8" x2="18" y2="13"/>
            </svg>`,
    people: `<svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M16 19v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="3.2"/>
              <path d="M22 19v-2a4 4 0 0 0-3-3.9"/>
              <path d="M16 4.2a3.2 3.2 0 0 1 0 6.2"/>
            </svg>`,
    yield: `<svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M3 13c0-3 4-5 9-5s9 2 9 5"/>
              <path d="M3 13v3a3 3 0 0 0 3 3h12a3 3 0 0 0 3-3v-3"/>
              <line x1="12" y1="3" x2="12" y2="8"/>
              <path d="M9.5 5.5c1-1.5 4-1.5 5 0"/>
            </svg>`,
  };

  function viewRecette(id) {
    const r = recipesById.get(id);
    if (!r) {
      return `
        <section class="empty-state" style="min-height:60vh; display:flex; align-items:center; justify-content:center;">
          <p>Recette introuvable.</p>
        </section>
      `;
    }
    const cat = categoryForRecipe(r.id);
    const catSlug = cat ? slugify(cat.name) : "";

    // Use overall recipe array order for prev/next, mirroring the Replit app's
    // findIndex-by-id ordering on the Ys array.
    const idx = recipes.findIndex((x) => x.id === r.id);
    const prev = idx > 0 ? recipes[idx - 1] : null;
    const next = idx < recipes.length - 1 ? recipes[idx + 1] : null;
    const cleanedNote = stripEmoji(r.notes);
    const checkedSet = loadChecked(r.id);

    return `
      <section class="recipe-page">
        <header class="recipe-header">
          <div class="recipe-header-inner">
            <nav class="recipe-crumbs">
              ${
                cat
                  ? `<a href="#/categorie/${encodeURIComponent(catSlug)}">${escapeHtml(cat.name)}</a>
                     <span class="sep">›</span>`
                  : ""
              }
              <span class="num">${escapeHtml(r.numberLabel)}</span>
            </nav>
            <h1 class="recipe-title">${escapeHtml(r.title)}</h1>
            <div class="recipe-orn">
              <div class="line"></div>
              <svg class="star" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M8 0l1.6 4.8H14.4l-3.8 3 1.6 4.8L8 9.6l-4.4 3 1.6-4.8L1 4.8h5.4z"/>
              </svg>
              <div class="line"></div>
            </div>
            ${renderInfoStrip(r.meta, r.id)}
          </div>
        </header>

        <div class="recipe-content">
          <div class="recipe-grid">
            <aside>
              <div class="ingredients-aside">
                <div class="ingredients-card">
                  <div class="section-label">
                    <span class="pip"></span>
                    <h2>Ingrédients</h2>
                    <span class="count">${(r.ingredients || []).length}</span>
                  </div>
                  <ul class="ingredients-list" data-recipe-id="${r.id}">
                    ${(r.ingredients || [])
                      .map((it, i) => {
                        const checked = checkedSet.has(i);
                        return `
                          <li class="${checked ? "is-checked" : ""}" data-ing-idx="${i}">
                            <button type="button" class="ing-check" role="checkbox" aria-checked="${checked}" aria-label="Cocher l'ingrédient">
                              <span class="dot"></span>
                              <svg class="check" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <polyline points="2 6 5 9 10 3"></polyline>
                              </svg>
                            </button>
                            <span class="text">${escapeHtml(it)}</span>
                          </li>
                        `;
                      })
                      .join("")}
                  </ul>
                </div>
                ${renderNutritionPanel(r.id)}
                ${
                  cat
                    ? `<a href="#/categorie/${encodeURIComponent(catSlug)}" class="cat-back">
                         <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
                         ${escapeHtml(cat.name)}
                       </a>`
                    : ""
                }
              </div>
            </aside>

            <main class="prep-section">
              <div class="section-label-inline">
                <span class="pip"></span>
                <h2>Préparation</h2>
              </div>
              <ol class="steps-list">
                ${(r.steps || [])
                  .map(
                    (step, i) => `
                      <li class="step-item">
                        <div class="connector"></div>
                        <div class="step-num">${i + 1}</div>
                        <div class="step-text"><p>${escapeHtml(step)}</p></div>
                      </li>
                    `,
                  )
                  .join("")}
              </ol>

              ${
                cleanedNote
                  ? `<aside class="note-box">
                       <p class="note-label">Note</p>
                       <p class="note-text">${escapeHtml(cleanedNote)}</p>
                     </aside>`
                  : ""
              }

              <footer class="recipe-foot">
                <nav class="recipe-nav">
                  ${
                    prev
                      ? `<a href="#/recette/${prev.id}" class="nav-card">
                           <span class="nav-label">
                             <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
                             Précédente
                           </span>
                           <span class="nav-title">${escapeHtml(prev.title)}</span>
                         </a>`
                      : `<div class="nav-card" style="border-color:transparent;"></div>`
                  }
                  ${
                    next
                      ? `<a href="#/recette/${next.id}" class="nav-card right">
                           <span class="nav-label">
                             Suivante
                             <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                           </span>
                           <span class="nav-title">${escapeHtml(next.title)}</span>
                         </a>`
                      : `<div class="nav-card" style="border-color:transparent;"></div>`
                  }
                </nav>
              </footer>
            </main>
          </div>
        </div>
      </section>
    `;
  }

  function renderFilterPanel() {
    // `est` flag adds a data-est attribute; the stylesheet uses ::after to
    // render the ≈ badge so we don't have to bypass label escaping.
    const chipBtn = (group, value, label, sel, extra = "", est = false) => `
      <button type="button" class="filter-chip ${sel ? "is-selected" : ""} ${extra}"
              data-filter-group="${group}" data-filter-value="${escapeHtml(value)}"
              ${est ? 'data-est="1"' : ""}
              aria-pressed="${sel ? "true" : "false"}">
        ${escapeHtml(label)}
      </button>`;

    const diffChips = DIFFICULTIES.map((d) =>
      chipBtn("difficulty", d, d, filterState.difficulties.has(d), `chip-difficulty chip-${d}`),
    ).join("");

    const timeChips = TIME_BUCKETS.map((b) =>
      chipBtn("time", b.key, `${b.label} · ${b.hint}`, filterState.timeBuckets.has(b.key)),
    ).join("");

    const tagSections = TAG_GROUPS.map((g) => {
      const sel = filterState.tagsByGroup[g.key];
      // Each chip in this group can carry a label override (TAG_LABELS) and an
      // "Estimé" suffix when the tag is derived from per-serving nutrition.
      const chips = g.tags
        .map((t) => {
          const label = TAG_LABELS[t] || t.replace(/-/g, " ");
          const isEst = nutrientTagSet.has(t);
          return chipBtn(`tag:${g.key}`, t, label, sel.has(t), "", isEst);
        })
        .join("");
      // For the régime group, surface the coverage caveat when nutrient-based
      // filters are part of the group. dietCoverage is null until diet_tags.json loads.
      let hint = "";
      if (g.key === "diet" && dietCoverage && nutrientTagSet.size) {
        const total = dietCoverage.total_recipes;
        const nut   = dietCoverage.nutrient_based;
        hint = `<span class="filter-group-hint">≈ Estimé d'après l'analyse nutritionnelle (${nut}/${total} recettes)</span>`;
      }
      return `
        <div class="filter-group">
          <span class="filter-group-label">${escapeHtml(g.label)}</span>
          ${hint}
          <div class="filter-chips">${chips}</div>
        </div>`;
    }).join("");

    const enviCount = enviFilterCount();
    const countText = enviCount === 0
      ? "Aucun critère sélectionné"
      : `${enviCount} critère${enviCount > 1 ? "s" : ""} sélectionné${enviCount > 1 ? "s" : ""}`;
    const showReset = enviCount > 0;

    return `
      <div class="filter-panel" id="filter-panel">
        <div class="filter-panel-head">
          <span class="filter-panel-title">Filtrer par envie</span>
          <div class="filter-panel-actions">
            <span class="filter-count">${escapeHtml(countText)}</span>
            <button type="button" id="filter-reset" class="filter-reset" ${showReset ? "" : "hidden"}>Effacer</button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-group-label">Difficulté</span>
          <div class="filter-chips">${diffChips}</div>
        </div>

        <div class="filter-group">
          <span class="filter-group-label">Temps total (préparation + cuisson)</span>
          <div class="filter-chips">${timeChips}</div>
        </div>

        ${tagSections}
      </div>
    `;
  }

  function renderIngredientPicker() {
    const sel = filterState.ingredients;
    // Initialize defaults on first render: groups open on desktop, all closed
    // on mobile. After that, remember user toggles via the `toggle` event.
    if (uiState.openIngGroups === null) {
      const isMobile =
        typeof window !== "undefined" &&
        window.matchMedia &&
        window.matchMedia("(max-width: 640px)").matches;
      uiState.openIngGroups = new Set(
        isMobile ? [] : INGREDIENT_GROUPS.map((g) => g.label),
      );
    }

    const sections = INGREDIENT_GROUPS.map((g) => {
      const groupSelCount = g.slugs.filter((s) => sel.has(s)).length;
      // Force open if the group has selections (so the user can see them).
      const isOpen = groupSelCount > 0 || uiState.openIngGroups.has(g.label);
      const tiles = g.slugs
        .map((slug) => {
          const def = INGREDIENTS[slug];
          if (!def) return "";
          const isSel = sel.has(slug);
          return `
            <button type="button"
                    class="ing-tile ${isSel ? "is-selected" : ""}"
                    data-ing-slug="${escapeHtml(slug)}"
                    aria-pressed="${isSel ? "true" : "false"}">
              <span class="ing-tile-icon">${def.icon || ING_DEFAULT_ICON}</span>
              <span class="ing-tile-label">${escapeHtml(def.label)}</span>
            </button>`;
        })
        .join("");
      const pill = groupSelCount > 0
        ? `<span class="ing-section-pill">${groupSelCount}</span>`
        : "";
      return `
        <details class="ing-section" data-group-label="${escapeHtml(g.label)}" ${isOpen ? "open" : ""}>
          <summary class="ing-section-summary">
            <span class="ing-section-label">${escapeHtml(g.label)}</span>
            ${pill}
            <svg class="ing-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
          </summary>
          <div class="ing-grid">${tiles}</div>
        </details>`;
    }).join("");

    const count = sel.size;
    const countLabel = count === 0
      ? "Aucun ingrédient sélectionné"
      : `${count} ingrédient${count > 1 ? "s" : ""} sélectionné${count > 1 ? "s" : ""}`;
    const showReset = count > 0;

    return `
      <div class="ing-panel" id="ing-panel">
        <div class="filter-panel-head">
          <span class="filter-panel-title">Par ingrédient</span>
          <div class="filter-panel-actions">
            <span class="ing-count">${escapeHtml(countLabel)}</span>
            <button type="button" id="ing-reset" class="filter-reset" ${showReset ? "" : "hidden"}>Effacer</button>
          </div>
        </div>
        ${sections}
      </div>
    `;
  }

  function viewRecherche() {
    // Restore filters + sort + query from sessionStorage before the panels
    // render, so the UI reflects the saved state on first paint.
    loadSearchState();
    return `
      <section class="search-page">
        <div class="container container-sm">
          <div class="search-bar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.3-4.3"></path>
            </svg>
            <input id="search-input" class="search-input" type="search" placeholder="Rechercher (ex. : carotte sel poivre)..." autofocus />
            <span class="search-hint">Plusieurs mots = recettes contenant <strong>tous</strong> les termes. Cumulez avec les filtres et les ingrédients ci-dessous.</span>
          </div>
          ${renderFilterPanel()}
          ${renderIngredientPicker()}
          <div id="search-results" class="search-results"></div>
        </div>
      </section>
    `;
  }

  function normalizeText(s) {
    return String(s ?? "")
      .toLowerCase()
      .replace(/œ/g, "oe")
      .replace(/æ/g, "ae")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "");
  }

  function parseSearchTerms(q) {
    // Split on whitespace, commas, "+", and treat "et"/"and" as separators.
    return normalizeText(q)
      .split(/[\s,+]+/)
      .map((t) => t.trim())
      .filter((t) => t && t !== "et" && t !== "and");
  }

  // ---------- active filters bar (chips with × to remove individually) ----------
  function makeActiveChip(kind, value, label) {
    return `<span class="active-chip" data-active-kind="${escapeHtml(kind)}" data-active-value="${escapeHtml(value)}">
      <span class="active-chip-label">${escapeHtml(label)}</span>
      <button type="button" class="active-x" aria-label="Retirer ${escapeHtml(label)}">×</button>
    </span>`;
  }

  function renderActiveFiltersBar() {
    const chips = [];
    for (const d of filterState.difficulties) {
      chips.push(makeActiveChip("difficulty", d, d));
    }
    for (const tbKey of filterState.timeBuckets) {
      const b = TIME_BUCKETS.find((x) => x.key === tbKey);
      if (b) chips.push(makeActiveChip("time", tbKey, `${b.label} ${b.hint}`));
    }
    for (const g of TAG_GROUPS) {
      for (const t of filterState.tagsByGroup[g.key]) {
        chips.push(makeActiveChip("tag:" + g.key, t, TAG_LABELS[t] || t.replace(/-/g, " ")));
      }
    }
    for (const slug of filterState.ingredients) {
      const def = INGREDIENTS[slug];
      if (def) chips.push(makeActiveChip("ingredient", slug, def.label));
    }
    if (chips.length === 0) return "";
    return `<div class="active-filters-bar" role="region" aria-label="Filtres actifs">${chips.join("")}</div>`;
  }

  function removeActiveFilter(kind, value) {
    if (kind === "difficulty") filterState.difficulties.delete(value);
    else if (kind === "time") filterState.timeBuckets.delete(value);
    else if (kind && kind.startsWith("tag:")) {
      const gk = kind.slice(4);
      const set = filterState.tagsByGroup[gk];
      if (set) set.delete(value);
    } else if (kind === "ingredient") filterState.ingredients.delete(value);
  }

  // ---------- result sorting ----------
  const SORT_OPTIONS = [
    { key: "numero",     label: "Par numéro" },
    { key: "alpha",      label: "A → Z" },
    { key: "time-asc",   label: "Plus rapide d'abord" },
    { key: "difficulty", label: "Plus facile d'abord" },
  ];
  const DIFFICULTY_ORDER = { facile: 0, moyen: 1, difficile: 2 };

  function sortResults(list) {
    const arr = list.slice();
    switch (uiState.sort) {
      case "alpha":
        arr.sort((a, b) =>
          String(a.title || "").localeCompare(String(b.title || ""), "fr", { sensitivity: "base" }),
        );
        break;
      case "time-asc":
        arr.sort((a, b) => totalMinutes(a.meta) - totalMinutes(b.meta));
        break;
      case "difficulty":
        arr.sort((a, b) => {
          const ad = DIFFICULTY_ORDER[a.meta && a.meta.difficulty];
          const bd = DIFFICULTY_ORDER[b.meta && b.meta.difficulty];
          return (ad == null ? 99 : ad) - (bd == null ? 99 : bd);
        });
        break;
      default: /* numero — keep recipes.json order */ break;
    }
    return arr;
  }

  function renderResultsHeader(count) {
    const optsHtml = SORT_OPTIONS.map(
      (o) =>
        `<option value="${escapeHtml(o.key)}" ${uiState.sort === o.key ? "selected" : ""}>${escapeHtml(o.label)}</option>`,
    ).join("");
    return `
      <div class="results-header">
        <p class="search-count">${count} recette${count > 1 ? "s" : ""} trouvée${count > 1 ? "s" : ""}</p>
        <div class="results-sort">
          <label for="search-sort">Trier&nbsp;:</label>
          <select id="search-sort" class="filter-select">${optsHtml}</select>
        </div>
      </div>`;
  }

  function matchesQuery(r, terms) {
    if (terms.length === 0) return true;
    const title = normalizeText(r.title);
    const ingredients = (r.ingredients || []).map(normalizeText);
    return terms.every(
      (t) => title.includes(t) || ingredients.some((i) => i.includes(t)),
    );
  }

  function searchRecipes(q) {
    const terms = parseSearchTerms(q);
    const filtersOn = anyFilterActive();
    if (terms.length === 0 && !filtersOn) return [];
    return recipes.filter((r) => matchesQuery(r, terms) && recipeMatchesFilters(r));
  }

  function renderSearchResults(q) {
    const out = $("#search-results");
    if (!out) return;
    const filtersOn = anyFilterActive();
    const activeBar = renderActiveFiltersBar();

    if (!q.trim() && !filtersOn) {
      out.innerHTML = `<p class="search-empty">Saisissez un mot-clé ou choisissez des filtres pour découvrir des recettes.</p>`;
      return;
    }
    const allResults = searchRecipes(q);
    if (allResults.length === 0) {
      const reason = q.trim()
        ? `Aucune recette ne correspond à "${escapeHtml(q)}"`
        : `Aucune recette ne correspond aux filtres choisis`;
      out.innerHTML = activeBar + `<p class="search-empty">${reason}.</p>`;
      return;
    }
    const results = sortResults(allResults);
    const header = renderResultsHeader(results.length);
    const cards = results
      .map((r) => {
        const cat = categoryForRecipe(r.id);
        const m = r.meta || {};
        const meta = [];
        if (m.difficulty) meta.push(`<span class="search-meta-chip chip-${escapeHtml(m.difficulty)}">${escapeHtml(m.difficulty)}</span>`);
        const total = totalMinutes(m);
        if (total > 0) meta.push(`<span class="search-meta-chip">${escapeHtml(formatMinutes(total) || "")}</span>`);
        for (const t of m.tags || []) meta.push(`<span class="search-meta-chip">${escapeHtml(t.replace(/-/g, " "))}</span>`);
        const metaRow = meta.length ? `<div class="search-card-meta">${meta.join("")}</div>` : "";
        return `
          <a href="#/recette/${r.id}" class="search-card">
            <div class="search-card-row">
              <div>
                <div class="num">${escapeHtml(r.numberLabel)}</div>
                <h3>${escapeHtml(r.title)}</h3>
                ${metaRow}
              </div>
              ${cat ? `<div class="search-card-cat">${escapeHtml(cat.name)}</div>` : ""}
            </div>
          </a>
        `;
      })
      .join("");
    out.innerHTML = activeBar + header + cards;
  }

  // ---------- render ----------
  function render() {
    const route = parseRoute();
    const root = $("#app");
    if (!root) return;

    const showNav = route.name !== "home";
    let body = "";
    switch (route.name) {
      case "home":
        body = viewHome();
        break;
      case "sommaire":
        body = viewSommaire();
        break;
      case "categorie":
        body = viewCategorie(route.slug);
        break;
      case "recette":
        body = viewRecette(route.id);
        break;
      case "recherche":
        body = viewRecherche();
        break;
      default:
        body = viewHome();
    }
    root.innerHTML = (showNav ? renderNav(route.name) : "") + body;
    document.documentElement.scrollTop = 0;

    // post-render binding
    if (route.name === "sommaire") {
      const expand = $("#toc-expand-all");
      const collapse = $("#toc-collapse-all");
      const allDetails = $$("details.toc-section", root);
      if (expand) expand.addEventListener("click", () => {
        allDetails.forEach((d) => { d.open = true; });
      });
      if (collapse) collapse.addEventListener("click", () => {
        allDetails.forEach((d) => { d.open = false; });
      });
    }

    if (route.name === "recherche") {
      // (state was restored by viewRecherche so panels rendered with it)
      const input = $("#search-input");
      if (input) {
        if (uiState.query) input.value = uiState.query;
        input.focus();
        let timer;
        input.addEventListener("input", (e) => {
          clearTimeout(timer);
          const v = e.target.value;
          uiState.query = v;
          timer = setTimeout(() => {
            saveSearchState();
            renderSearchResults(v);
          }, 120);
        });
      }

      const refreshPanel = () => {
        const p = $("#filter-panel");
        if (!p) return;
        p.outerHTML = renderFilterPanel();
        bindFilterPanel();
      };
      const refreshIngPanel = () => {
        const p = $("#ing-panel");
        if (!p) return;
        p.outerHTML = renderIngredientPicker();
        bindIngPanel();
      };
      const refreshAll = () => {
        refreshPanel();
        refreshIngPanel();
        renderSearchResults(uiState.query);
      };
      const bindFilterPanel = () => {
        const p = $("#filter-panel");
        if (!p) return;
        $$(".filter-chip", p).forEach((btn) => {
          btn.addEventListener("click", () => {
            const group = btn.getAttribute("data-filter-group");
            const value = btn.getAttribute("data-filter-value");
            if (group === "difficulty") toggleSet(filterState.difficulties, value);
            else if (group === "time") toggleSet(filterState.timeBuckets, value);
            else if (group.startsWith("tag:")) {
              const gk = group.slice(4);
              toggleSet(filterState.tagsByGroup[gk], value);
            }
            saveSearchState();
            refreshPanel();
            renderSearchResults(uiState.query);
          });
        });
        const reset = $("#filter-reset", p);
        if (reset) {
          reset.addEventListener("click", () => {
            resetEnviFilters();
            saveSearchState();
            refreshPanel();
            renderSearchResults(uiState.query);
          });
        }
      };
      const bindIngPanel = () => {
        const p = $("#ing-panel");
        if (!p) return;
        $$(".ing-tile", p).forEach((btn) => {
          btn.addEventListener("click", () => {
            const slug = btn.getAttribute("data-ing-slug");
            if (!slug) return;
            toggleSet(filterState.ingredients, slug);
            saveSearchState();
            refreshIngPanel();
            renderSearchResults(uiState.query);
          });
        });
        $$("details.ing-section", p).forEach((d) => {
          d.addEventListener("toggle", () => {
            const label = d.getAttribute("data-group-label");
            if (!label || !uiState.openIngGroups) return;
            if (d.open) uiState.openIngGroups.add(label);
            else uiState.openIngGroups.delete(label);
            saveSearchState();
          });
        });
        const ingReset = $("#ing-reset", p);
        if (ingReset) {
          ingReset.addEventListener("click", () => {
            resetIngredients();
            saveSearchState();
            refreshIngPanel();
            renderSearchResults(uiState.query);
          });
        }
      };

      // Active filter chip × buttons + sort dropdown live inside #search-results,
      // which is re-rendered on every filter change. Use event delegation.
      const resultsRoot = $("#search-results");
      if (resultsRoot) {
        resultsRoot.addEventListener("click", (ev) => {
          const x = ev.target.closest(".active-x");
          if (!x) return;
          ev.preventDefault();
          ev.stopPropagation();
          const chip = x.closest(".active-chip");
          if (!chip) return;
          const kind = chip.getAttribute("data-active-kind");
          const value = chip.getAttribute("data-active-value");
          removeActiveFilter(kind, value);
          saveSearchState();
          refreshAll();
        });
        resultsRoot.addEventListener("change", (ev) => {
          const sel = ev.target.closest("#search-sort");
          if (!sel) return;
          uiState.sort = sel.value;
          saveSearchState();
          renderSearchResults(uiState.query);
        });
      }

      bindFilterPanel();
      bindIngPanel();
      renderSearchResults(uiState.query);
    }

    // Recipe page: wire up checkable ingredients with localStorage persistence.
    if (route.name === "recette") {
      const list = $(".ingredients-list[data-recipe-id]", root);
      if (list) {
        const recipeId = parseInt(list.getAttribute("data-recipe-id"), 10);
        list.addEventListener("click", (ev) => {
          const btn = ev.target.closest(".ing-check");
          if (!btn) return;
          const li = btn.closest("li[data-ing-idx]");
          if (!li) return;
          const idx = parseInt(li.getAttribute("data-ing-idx"), 10);
          const set = loadChecked(recipeId);
          if (set.has(idx)) {
            set.delete(idx);
            li.classList.remove("is-checked");
            btn.setAttribute("aria-checked", "false");
          } else {
            set.add(idx);
            li.classList.add("is-checked");
            btn.setAttribute("aria-checked", "true");
          }
          saveChecked(recipeId, set);
        });
      }
    }

    // intercept clicks on internal hash links to enable smooth feel and re-trigger render even for same hash
    $$("a[href^='#/']", root).forEach((a) => {
      a.addEventListener("click", (ev) => {
        const href = a.getAttribute("href");
        if (href === "#" + location.hash.replace(/^#/, "")) {
          ev.preventDefault();
          render();
        }
      });
    });
  }

  // ---------- bootstrap ----------
  window.addEventListener("hashchange", render);

  // Reactive auth: re-render the header whenever the session changes (login,
  // logout, token refresh). When auth isn't configured, onAuthChange fires
  // once with null and we move on — no-op.
  onAuthChange((session) => {
    const before = !!authSession;
    authSession = session || null;
    const after = !!authSession;
    if (before !== after && document.getElementById("app")) {
      render();
    }
  });

  // Delegated click handler for the Déconnexion button in the header.
  document.addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="signout"]');
    if (!btn) return;
    e.preventDefault();
    authSignOut();
  });

  document.addEventListener("DOMContentLoaded", async () => {
    const root = $("#app");
    if (!root) return;
    try {
      await loadData();
      render();
    } catch (e) {
      console.error(e);
      root.innerHTML = `<div class="empty-state"><p>Impossible de charger les recettes.</p></div>`;
    }
  });
})();
