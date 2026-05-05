// Netlify Function: POST /.netlify/functions/publish
//
// Materializes the live Supabase recipes table into recipes.json and commits
// it back to GitHub. Triggered by the "Publier" button on the admin dashboard.
//
// Auth flow:
//   1. Caller passes their Supabase JWT in the Authorization header.
//   2. We verify the JWT against the project (cheap — Supabase signs with the
//      anon key's secret) and look up the user's email.
//   3. We check that the email exists in allowed_emails with is_admin=true.
//   4. If all good, we fetch every row of the recipes table, sort by id, and
//      shape them back into the recipes.json schema.
//   5. We GET the current recipes.json blob's SHA from GitHub, then PUT the
//      new content. GitHub creates a commit automatically.
//   6. Netlify auto-redeploys when the commit lands on main.
//
// Required environment variables (Netlify → Site settings → Environment):
//   - SUPABASE_URL                 (same as in assets/auth-config.js)
//   - SUPABASE_ANON_KEY            (same)
//   - GITHUB_TOKEN                 (PAT with Contents: read+write on the repo)
//   - GITHUB_REPO   (default: "jeremyprincerich/new-app")
//   - GITHUB_BRANCH (default: "main")
//   - GITHUB_FILE   (default: "recipes.json")
//   - COMMIT_AUTHOR_NAME / COMMIT_AUTHOR_EMAIL (optional; default to "Cahier Bot")

import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL      = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const GITHUB_TOKEN      = process.env.GITHUB_TOKEN;
const GITHUB_REPO       = process.env.GITHUB_REPO   || "jeremyprincerich/new-app";
const GITHUB_BRANCH     = process.env.GITHUB_BRANCH || "main";
const GITHUB_FILE       = process.env.GITHUB_FILE   || "recipes.json";
const AUTHOR_NAME       = process.env.COMMIT_AUTHOR_NAME  || "Cahier Bot";
const AUTHOR_EMAIL      = process.env.COMMIT_AUTHOR_EMAIL || "noreply@cahier.local";

function jsonResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      // CORS — we host on the same origin so this is largely moot, but it
      // makes the function callable from preview environments too.
      "Access-Control-Allow-Origin":  "*",
      "Access-Control-Allow-Headers": "Authorization, Content-Type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
    },
    body: JSON.stringify(body),
  };
}

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") return jsonResponse(204, {});
  if (event.httpMethod !== "POST")    return jsonResponse(405, { error: "Method not allowed" });

  if (!SUPABASE_URL || !SUPABASE_ANON_KEY || !GITHUB_TOKEN) {
    return jsonResponse(500, {
      error: "Configuration manquante côté serveur (SUPABASE_URL / SUPABASE_ANON_KEY / GITHUB_TOKEN).",
    });
  }

  // ---- 1. Validate the caller ----
  const authHeader = event.headers.authorization || event.headers.Authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return jsonResponse(401, { error: "Token d'authentification manquant." });
  }
  const userJwt = authHeader.slice("Bearer ".length).trim();

  // Pass the user's JWT to the supabase client so RLS treats requests as
  // that user. allowed_emails RLS policy will only return rows for admins.
  const sb = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${userJwt}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: userResp, error: userErr } = await sb.auth.getUser(userJwt);
  if (userErr || !userResp?.user) {
    return jsonResponse(401, { error: "Session invalide ou expirée." });
  }
  const email = (userResp.user.email || "").toLowerCase();

  const { data: wlRow, error: wlErr } = await sb
    .from("allowed_emails")
    .select("is_admin")
    .eq("email", email)
    .maybeSingle();
  if (wlErr || !wlRow || !wlRow.is_admin) {
    return jsonResponse(403, { error: "Seuls les administrateurs peuvent publier." });
  }

  // ---- 2. Pull every recipe and rebuild the JSON ----
  const { data: rows, error: rErr } = await sb
    .from("recipes")
    .select("id, data")
    .order("id", { ascending: true });
  if (rErr) return jsonResponse(500, { error: "Erreur de lecture: " + rErr.message });

  // Each row's `data` is the recipe object. Project to recipes.json schema.
  // Defensive: ensure id matches between row and data.
  const recipes = (rows || []).map((r) => {
    const rec = { ...(r.data || {}) };
    if (rec.id !== r.id) rec.id = r.id;
    return rec;
  });
  // Match the formatting of the existing recipes.json (pretty-printed, 2-space).
  const newContent = JSON.stringify(recipes, null, 2) + "\n";
  const newContentB64 = Buffer.from(newContent, "utf8").toString("base64");

  // ---- 3. GET current file SHA from GitHub ----
  const ghBase = `https://api.github.com/repos/${GITHUB_REPO}/contents/${encodeURIComponent(GITHUB_FILE)}`;
  const ghHeaders = {
    "Authorization": `Bearer ${GITHUB_TOKEN}`,
    "Accept":        "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent":    "cahier-publish-fn",
  };

  let currentSha = null;
  let currentContentB64 = null;
  const getResp = await fetch(`${ghBase}?ref=${encodeURIComponent(GITHUB_BRANCH)}`, { headers: ghHeaders });
  if (getResp.ok) {
    const meta = await getResp.json();
    currentSha = meta.sha;
    currentContentB64 = (meta.content || "").replace(/\s+/g, "");
  } else if (getResp.status !== 404) {
    const txt = await getResp.text();
    return jsonResponse(502, { error: `GitHub GET a échoué (${getResp.status}): ${txt.slice(0, 300)}` });
  }

  // No-op shortcut: if the new content is byte-for-byte identical, skip the
  // commit (avoids empty deploys and useless history rows).
  if (currentContentB64 && currentContentB64 === newContentB64.replace(/\s+/g, "")) {
    return jsonResponse(200, {
      committed: recipes.length,
      changed: false,
      message: "Aucun changement par rapport à la dernière publication.",
    });
  }

  // ---- 4. PUT new content (creates a commit) ----
  const commitMessage = `Publish recipes.json from editor (${recipes.length} recipes, by ${email})`;
  const putBody = {
    message: commitMessage,
    content: newContentB64,
    branch:  GITHUB_BRANCH,
    committer: { name: AUTHOR_NAME, email: AUTHOR_EMAIL },
    author:    { name: AUTHOR_NAME, email: AUTHOR_EMAIL },
  };
  if (currentSha) putBody.sha = currentSha;

  const putResp = await fetch(ghBase, {
    method: "PUT",
    headers: { ...ghHeaders, "Content-Type": "application/json" },
    body: JSON.stringify(putBody),
  });
  if (!putResp.ok) {
    const txt = await putResp.text();
    return jsonResponse(502, { error: `GitHub PUT a échoué (${putResp.status}): ${txt.slice(0, 300)}` });
  }
  const putJson = await putResp.json();

  return jsonResponse(200, {
    committed: recipes.length,
    changed: true,
    commit_sha: putJson.commit?.sha,
    commit_url: putJson.commit?.html_url,
  });
}
