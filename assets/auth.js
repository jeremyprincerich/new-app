// ESM module loaded by login.html, auth-callback.html, and app.js.
// Wraps the Supabase JS client with the small set of helpers the app needs:
//   - getSession() / onSessionChange() — current user + reactive updates
//   - sendMagicLink(email) — kicks off passwordless login
//   - signOut()
//   - isAdmin() — reads allowed_emails to check the is_admin flag
//
// We pull supabase-js from esm.sh to keep the site build-step-free, matching
// the existing zero-dependency philosophy described in CLAUDE.md.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";
import { SUPABASE_URL, SUPABASE_ANON_KEY, isAuthConfigured } from "./auth-config.js";

const CONFIGURED = isAuthConfigured();

// Lazy: only create the real client when configured. Keeps "auth not set up
// yet" deploys (e.g. previews before the user has run db/SETUP.md) from
// breaking the public site.
export const supabase = CONFIGURED
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        // Magic-link redirects come back to /auth-callback.html, where
        // supabase-js parses the URL fragment and persists the session.
        flowType: "pkce",
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null;

export function isConfigured() {
  return CONFIGURED;
}

/** Returns the current Session object, or null if signed out / not configured. */
export async function getSession() {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) {
    console.warn("getSession error", error);
    return null;
  }
  return data.session ?? null;
}

/** Subscribe to session changes. Callback receives the current session (or null).
 *  Returns an unsubscribe function. */
export function onSessionChange(cb) {
  if (!supabase) {
    cb(null);
    return () => {};
  }
  // Fire once with the initial state for callers that just mounted
  getSession().then(cb);
  const { data: sub } = supabase.auth.onAuthStateChange((_evt, session) => cb(session));
  return () => sub.subscription.unsubscribe();
}

/** Send a magic link to the email. Throws on error so the caller can surface a message. */
export async function sendMagicLink(email) {
  if (!supabase) throw new Error("Auth non configuré (voir db/SETUP.md)");
  const trimmed = (email || "").trim().toLowerCase();
  if (!trimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    throw new Error("Adresse courriel invalide");
  }
  const { error } = await supabase.auth.signInWithOtp({
    email: trimmed,
    options: {
      emailRedirectTo: new URL("/auth-callback.html", location.origin).toString(),
      // Don't auto-create accounts — the DB trigger blocks non-whitelisted
      // emails, but this gives a cleaner error before the round-trip.
      shouldCreateUser: true,
    },
  });
  if (error) {
    // Supabase wraps the trigger's "Email not authorized" as a generic 500.
    // The whitelist trigger is the most likely cause if signup fails.
    if (/not authorized/i.test(error.message) || error.status === 500) {
      throw new Error("Cette adresse n'est pas autorisée à se connecter. Demandez à un administrateur de l'ajouter.");
    }
    throw new Error(error.message || "Échec de l'envoi du courriel");
  }
}

export async function signOut() {
  if (!supabase) return;
  await supabase.auth.signOut();
}

/** Return true if the current user is flagged is_admin in allowed_emails. */
export async function isAdmin() {
  if (!supabase) return false;
  const session = await getSession();
  if (!session) return false;
  const { data, error } = await supabase
    .from("allowed_emails")
    .select("is_admin")
    .eq("email", session.user.email.toLowerCase())
    .maybeSingle();
  if (error || !data) return false;
  return !!data.is_admin;
}
