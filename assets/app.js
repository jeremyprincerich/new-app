// Cahier de Recettes — vanilla SPA matching the Replit React version.
// Routes (hash-based for static hosting):
//   #/                     -> hero / book cover
//   #/sommaire             -> Table des Matières (all categories + recipes)
//   #/categorie/:slug      -> Category landing
//   #/recette/:id          -> Recipe detail
//   #/recherche            -> Search

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

  // ---------- data ----------
  let recipes = [];
  let categories = [];
  let recipesById = new Map();
  let categoryBySlug = new Map();

  async function loadData() {
    const [r, c] = await Promise.all([
      fetch("recipes.json").then((x) => x.json()),
      fetch("categories.json").then((x) => x.json()),
    ]);
    recipes = r;
    categories = c;
    recipesById = new Map(r.map((x) => [x.id, x]));
    categoryBySlug = new Map(c.map((cat) => [slugify(cat.name), cat]));
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
          </header>
          <div class="toc-sections">
            ${categories
              .map((cat) => {
                const items = recipesInCategory(cat);
                const slug = slugify(cat.name);
                return `
                  <section class="toc-section">
                    <div class="toc-cat-head">
                      <a href="#/categorie/${encodeURIComponent(slug)}" class="toc-cat-link">
                        <span class="toc-cat-icon">${categoryIcon(slug)}</span>
                        <h2 class="toc-cat-name">${escapeHtml(cat.name)}</h2>
                      </a>
                      <span class="toc-cat-count">${items.length} recettes</span>
                    </div>
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
                  </section>
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

  // Render the info strip (prep / cook / servings) below the recipe title.
  // Each badge only renders if its value is present, so recipes with no
  // metadata fall back gracefully to the original ornament-only header.
  function renderInfoStrip(meta) {
    if (!meta) return "";
    const items = [];
    const prep = formatMinutes(meta.prepMinutes);
    const cook = formatMinutes(meta.cookMinutes);
    const serv = typeof meta.servings === "number" ? meta.servings : null;
    if (prep) items.push({ label: "Préparation", value: prep, icon: "knife" });
    if (cook) items.push({ label: "Cuisson", value: cook, icon: "clock" });
    if (serv !== null) {
      items.push({
        label: serv > 1 ? "Portions" : "Portion",
        value: String(serv),
        icon: "people",
      });
    }
    if (items.length === 0) return "";
    return `
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
            ${renderInfoStrip(r.meta)}
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

  function viewRecherche() {
    // initial render — input is interactive after mount
    return `
      <section class="search-page">
        <div class="container container-sm">
          <div class="search-bar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.3-4.3"></path>
            </svg>
            <input id="search-input" class="search-input" type="search" placeholder="Rechercher (ex. : carotte sel poivre)..." autofocus />
            <span class="search-hint">Plusieurs mots = recettes contenant <strong>tous</strong> les termes</span>
          </div>
          <div id="search-results" class="search-results"></div>
        </div>
      </section>
    `;
  }

  function normalizeText(s) {
    return String(s ?? "")
      .toLowerCase()
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

  function searchRecipes(q) {
    const terms = parseSearchTerms(q);
    if (terms.length === 0) return [];
    return recipes.filter((r) => {
      const title = normalizeText(r.title);
      const ingredients = (r.ingredients || []).map(normalizeText);
      return terms.every(
        (t) => title.includes(t) || ingredients.some((i) => i.includes(t)),
      );
    });
  }

  function renderSearchResults(q) {
    const out = $("#search-results");
    if (!out) return;
    if (!q.trim()) {
      out.innerHTML = "";
      return;
    }
    const results = searchRecipes(q);
    if (results.length === 0) {
      out.innerHTML = `<p class="search-empty">Aucune recette ne correspond à "${escapeHtml(q)}".</p>`;
      return;
    }
    out.innerHTML = results
      .map((r) => {
        const cat = categoryForRecipe(r.id);
        return `
          <a href="#/recette/${r.id}" class="search-card">
            <div class="search-card-row">
              <div>
                <div class="num">${escapeHtml(r.numberLabel)}</div>
                <h3>${escapeHtml(r.title)}</h3>
              </div>
              ${cat ? `<div class="search-card-cat">${escapeHtml(cat.name)}</div>` : ""}
            </div>
          </a>
        `;
      })
      .join("");
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
    if (route.name === "recherche") {
      const input = $("#search-input");
      if (input) {
        input.focus();
        let timer;
        input.addEventListener("input", (e) => {
          clearTimeout(timer);
          const v = e.target.value;
          timer = setTimeout(() => renderSearchResults(v), 120);
        });
      }
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
