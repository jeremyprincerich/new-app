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
                  <ul class="ingredients-list">
                    ${(r.ingredients || [])
                      .map(
                        (it) => `
                          <li>
                            <span class="dot"></span>
                            <span class="text">${escapeHtml(it)}</span>
                          </li>
                        `,
                      )
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
            <input id="search-input" class="search-input" type="search" placeholder="Rechercher une recette ou un ingrédient..." autofocus />
          </div>
          <div id="search-results" class="search-results"></div>
        </div>
      </section>
    `;
  }

  function searchRecipes(q) {
    const term = q.trim().toLowerCase();
    if (!term) return [];
    return recipes.filter((r) => {
      if (r.title.toLowerCase().includes(term)) return true;
      if ((r.ingredients || []).some((i) => i.toLowerCase().includes(term)))
        return true;
      return false;
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
