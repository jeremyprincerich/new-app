// Thin wrapper around Supabase queries that the editor uses to read/write
// recipes, edit history, and the email whitelist. Centralizing these keeps
// app.js free of supabase-specific code and makes it easy to mock for tests.

import { supabase, isConfigured, getSession } from "./auth.js";

function notReady() {
  return new Error("Auth/database non configuré — voir db/SETUP.md");
}

/** Fetch one recipe from the DB. Returns the JSONB `data` field (the same
 *  shape as recipes.json entries). */
export async function loadRecipe(id) {
  if (!isConfigured()) throw notReady();
  const { data, error } = await supabase
    .from("recipes")
    .select("id, data, updated_at, updated_by")
    .eq("id", id)
    .maybeSingle();
  if (error) throw error;
  return data;     // { id, data, updated_at, updated_by } — caller pulls .data
}

/** Save a full recipe back to the DB. The audit trigger fires automatically
 *  and writes a before/after row to edit_log. */
export async function saveRecipe(id, recipe, comment = null) {
  if (!isConfigured()) throw notReady();
  const session = await getSession();
  if (!session) throw new Error("Vous devez être connecté pour modifier une recette.");

  // The trigger reads new.updated_by — set it explicitly so the audit log
  // captures who saved.
  const updates = {
    data: recipe,
    updated_at: new Date().toISOString(),
    updated_by: session.user.id,
  };
  const { error } = await supabase
    .from("recipes")
    .update(updates)
    .eq("id", id);
  if (error) throw error;

  // Optional: write a comment alongside the most recent edit_log row. We do
  // this in a follow-up update so the trigger doesn't have to know about it.
  if (comment && comment.trim()) {
    const { data: last } = await supabase
      .from("edit_log")
      .select("id")
      .eq("recipe_id", id)
      .order("edited_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (last) {
      await supabase.from("edit_log").update({ comment: comment.trim() }).eq("id", last.id);
    }
  }
}

/** Pull the full recipes table — used by the dashboard QA queue and by the
 *  publish function to materialize recipes.json. Sorted by id ascending so
 *  the published JSON has stable ordering. */
export async function loadAllRecipes() {
  if (!isConfigured()) throw notReady();
  const { data, error } = await supabase
    .from("recipes")
    .select("id, data, updated_at, updated_by")
    .order("id", { ascending: true });
  if (error) throw error;
  return data || [];
}

/** Recent edits for the dashboard. Joins through the v_recent_edits view that
 *  schema.sql created so the editor email + recipe title come pre-rendered. */
export async function loadRecentEdits(limit = 50) {
  if (!isConfigured()) throw notReady();
  const { data, error } = await supabase
    .from("v_recent_edits")
    .select("*")
    .limit(limit);
  if (error) throw error;
  return data || [];
}

/** All allowed_emails rows — admin-only, RLS enforces this.  */
export async function loadAllowedEmails() {
  if (!isConfigured()) throw notReady();
  const { data, error } = await supabase
    .from("allowed_emails")
    .select("email, is_admin, added_at")
    .order("added_at", { ascending: true });
  if (error) throw error;
  return data || [];
}

export async function addAllowedEmail(email, isAdmin = false) {
  if (!isConfigured()) throw notReady();
  const trimmed = (email || "").trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) throw new Error("Adresse courriel invalide.");
  const session = await getSession();
  const { error } = await supabase
    .from("allowed_emails")
    .insert({ email: trimmed, is_admin: !!isAdmin, added_by: session?.user?.id ?? null });
  if (error) throw error;
}

export async function removeAllowedEmail(email) {
  if (!isConfigured()) throw notReady();
  const trimmed = (email || "").trim().toLowerCase();
  const { error } = await supabase
    .from("allowed_emails")
    .delete()
    .eq("email", trimmed);
  if (error) throw error;
}

/** Roll a recipe back to its state before a specific edit_log entry.
 *  Used by the "Annuler cette modification" link in the edit history. */
export async function rollbackEdit(editLogId) {
  if (!isConfigured()) throw notReady();
  // Pull the before_data from the chosen log entry
  const { data: entry, error: e1 } = await supabase
    .from("edit_log")
    .select("recipe_id, before_data")
    .eq("id", editLogId)
    .maybeSingle();
  if (e1) throw e1;
  if (!entry || !entry.before_data) {
    throw new Error("Impossible de revenir en arrière (aucun état antérieur enregistré).");
  }
  await saveRecipe(entry.recipe_id, entry.before_data, "Annulation d'une modification précédente");
}
